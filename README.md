# KMC Care Analytics

An end-to-end analytics project on **synthetic** Kangaroo Mother Care (KMC) program
data. It takes raw field-app style exports, runs them through a SQL modeling layer,
and serves decision-ready views to program and M&E teams in a Streamlit dashboard.

> **This is a portfolio project. All data is randomly generated — it is not real
> patient data and none of the numbers describe any real organisation or outcome.**
> It's built to demonstrate the stack an analytics/BI engineer would own day to day.

**Live dashboard:** _add your Streamlit Cloud link here after deploying_
**What it shows:** coverage KPIs · KMC adherence trends · hospital comparison ·
a data-quality worklist that flags issues before they reach a report.

---

## Why this project

Newborn-care programs like this generate operational data from the field (admissions,
daily KMC sessions, discharge outcomes) that only creates value once it's modelled
cleanly and put in front of the people making decisions. This repo is a small,
honest version of that whole path — the same shape of problem as owning a real
dashboard-and-warehouse stack.

## Architecture

```
 raw app exports (CSV)          SQL modeling layer (sql/)              serving
 ┌──────────────────┐      ┌───────────────────────────────┐    ┌──────────────┐
 │ admissions.csv   │      │ 01 stg_admissions   (clean)    │    │              │
 │ kmc_sessions.csv │ ───▶ │ 02 stg_kmc_sessions (dedupe)   │──▶ │  Streamlit   │
 │ outcomes.csv     │      │ 03 stg_outcomes                │    │  dashboard   │
 │ hospitals.csv    │      │ 04 dim_hospital                │    │  (app.py)    │
 └──────────────────┘      │ 05 fct_kmc_daily    (grain)    │    │              │
                           │ 06 mart_admissions  (join)     │    └──────────────┘
                           │ 07 data_quality_flags          │
                           └───────────────────────────────┘
```

- **Staging → dimensions/facts → marts**, the standard analytics-engineering layering,
  with each model in its own numbered `.sql` file (dependency order).
- The SQL runs live on **DuckDB** so the app hosts for free with no warehouse cost.
  It's written to be **portable to BigQuery** — the only change is `TRY_CAST` → `SAFE_CAST`.
- A dedicated **data-quality model** surfaces missing/implausible weights, admissions
  with no KMC recorded, and missing outcomes as an actionable worklist.

## Stack

`Python` · `SQL` (BigQuery-portable) · `DuckDB` · `Streamlit` · `Plotly` · `pytest`

## Run locally

```bash
pip install -r requirements.txt
python generate_data.py     # writes synthetic CSVs to data/raw/
streamlit run app.py
```

Run the tests (grain, de-dup, referential integrity, DQ):

```bash
python -m pytest -q          # or: python test_pipeline.py
```

## Deploy a shareable link (free)

1. Push this repo to GitHub (public).
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo, set
   `app.py` as the entry point, and deploy.
3. Commit `data/raw/` (the generated CSVs) so the hosted app has data, **or** the app
   will build it on first run if you add a generate step. Paste the resulting
   `*.streamlit.app` URL at the top of this README.

## Repo layout

```
generate_data.py     synthetic data generator (deterministic, seeded)
pipeline.py          runs the SQL models over the CSVs via DuckDB
app.py               Streamlit dashboard
sql/                 the modeling layer, one model per file
test_pipeline.py     data-integrity tests
data/raw/            generated CSV inputs
```

## Notes & honesty

The outcome relationships in the synthetic data are generated with a simple rule
(more KMC and higher birth weight → better modelled outcomes) so the dashboard has
a coherent story to tell. That relationship is **built into the fake data on purpose
for demonstration** — it is not evidence about KMC. The real-world evidence base for
KMC is established separately in the clinical literature.
