"""
pipeline.py
-----------
Builds the analytics models by running the SQL layer (sql/*.sql) over the raw
CSV exports using DuckDB. DuckDB is used so the whole pipeline runs live in a
free-hosted app with zero warehouse cost; the SQL is written to be portable to
BigQuery (swap TRY_CAST -> SAFE_CAST).

The order of the numbered SQL files is the dependency order:
    raw_* (CSV)  ->  stg_*  ->  dim_/fct_  ->  mart_/quality
"""

from __future__ import annotations
import glob
import os
import duckdb
import pandas as pd

BASE = os.path.dirname(__file__)
RAW = os.path.join(BASE, "data", "raw")
SQL_DIR = os.path.join(BASE, "sql")


def build() -> dict[str, pd.DataFrame]:
    """Run the full pipeline and return the modelled tables as DataFrames."""
    # generate the synthetic CSVs on first run (e.g. fresh cloud deploy) if absent
    if not os.path.exists(os.path.join(RAW, "admissions.csv")):
        import generate_data
        generate_data.main()

    con = duckdb.connect(database=":memory:")

    # 1. load raw app exports as base tables
    for name in ["admissions", "kmc_sessions", "outcomes", "hospitals"]:
        con.execute(
            f"CREATE TABLE raw_{name} AS "
            f"SELECT * FROM read_csv_auto('{os.path.join(RAW, name + '.csv')}', header=true)"
        )

    # 2. execute the SQL models in numbered order
    for path in sorted(glob.glob(os.path.join(SQL_DIR, "*.sql"))):
        with open(path, "r", encoding="utf-8") as fh:
            con.execute(fh.read())

    # 3. return the tables the dashboard consumes
    return {
        "admissions": con.execute("SELECT * FROM mart_admissions").df(),
        "kmc_daily": con.execute("SELECT * FROM fct_kmc_daily").df(),
        "hospitals": con.execute("SELECT * FROM dim_hospital").df(),
        "dq": con.execute("SELECT * FROM data_quality_flags").df(),
    }


if __name__ == "__main__":
    tables = build()
    for name, df in tables.items():
        print(f"{name:12s}: {len(df):>6,} rows, {df.shape[1]} cols")
