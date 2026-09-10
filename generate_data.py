"""
generate_data.py
------------------
Creates SYNTHETIC raw data that mimics what a Kangaroo Mother Care (KMC)
field application might export: newborn admissions, daily KMC sessions, and
discharge outcomes across several district hospitals.

Nothing here is real patient data. Values are randomly generated with plausible
distributions purely to demonstrate a data pipeline and dashboard. A few
deliberate data-quality problems (missing weights, implausible values, duplicate
rows) are injected so the dashboard's data-quality checks have something to catch.

Run:  python generate_data.py
Output: data/raw/admissions.csv, kmc_sessions.csv, outcomes.csv
"""

from __future__ import annotations
import os
import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)  # deterministic output
RAW_DIR = os.path.join(os.path.dirname(__file__), "data", "raw")

# ---------------------------------------------------------------------------
# Reference data: hospitals across two states (mirrors Ansh's RJ -> MP scale-up)
# ---------------------------------------------------------------------------
HOSPITALS = [
    # hospital_id, name, district, state, sncu_beds, base_adherence
    ("H01", "Jaipur DH",        "Jaipur",     "Rajasthan",      20, 0.82),
    ("H02", "Jodhpur DH",       "Jodhpur",    "Rajasthan",      18, 0.74),
    ("H03", "Udaipur DH",       "Udaipur",    "Rajasthan",      16, 0.88),
    ("H04", "Kota DH",          "Kota",       "Rajasthan",      14, 0.63),
    ("H05", "Bikaner DH",       "Bikaner",    "Rajasthan",      12, 0.71),
    ("H06", "Ajmer DH",         "Ajmer",      "Rajasthan",      15, 0.79),
    ("H07", "Alwar DH",         "Alwar",      "Rajasthan",      10, 0.58),
    ("H08", "Bharatpur DH",     "Bharatpur",  "Rajasthan",      12, 0.69),
    ("H09", "Bhopal DH",        "Bhopal",     "Madhya Pradesh", 18, 0.66),
    ("H10", "Indore DH",        "Indore",     "Madhya Pradesh", 20, 0.77),
    ("H11", "Gwalior DH",       "Gwalior",    "Madhya Pradesh", 14, 0.61),
    ("H12", "Jabalpur DH",      "Jabalpur",   "Madhya Pradesh", 12, 0.72),
]

START = pd.Timestamp("2025-01-01")
END = pd.Timestamp("2025-12-31")
CAREGIVERS = ["Mother", "Father", "Grandmother", "Other"]
CAREGIVER_P = [0.78, 0.12, 0.07, 0.03]


def make_admissions() -> pd.DataFrame:
    rows = []
    aid = 1
    for hid, _, _, _, beds, _ in HOSPITALS:
        # busier hospitals (more beds) admit more babies
        n = int(RNG.normal(beds * 22, beds * 3))
        for _ in range(n):
            admit = START + pd.Timedelta(days=int(RNG.integers(0, (END - START).days)))
            # birth weight (grams): centred ~2100 so plenty of low-birth-weight cases
            bw = int(np.clip(RNG.normal(2100, 500), 700, 4200))
            ga = int(np.clip(RNG.normal(35, 2.5), 26, 42))  # gestational weeks
            rows.append({
                "admission_id": f"A{aid:05d}",
                "hospital_id": hid,
                "admit_date": admit.date().isoformat(),
                "birth_weight_g": bw,
                "gestational_age_wks": ga,
                "sex": RNG.choice(["F", "M"], p=[0.485, 0.515]),
            })
            aid += 1
    df = pd.DataFrame(rows)

    # --- inject data-quality issues ---
    miss = RNG.choice(df.index, size=int(len(df) * 0.02), replace=False)
    df.loc[miss, "birth_weight_g"] = np.nan                       # missing weights
    bad = RNG.choice(df.index, size=8, replace=False)
    df.loc[bad, "birth_weight_g"] = RNG.choice([50, 60, 9999], size=8)  # implausible
    return df


def make_sessions(adm: pd.DataFrame) -> pd.DataFrame:
    adh = {h[0]: h[5] for h in HOSPITALS}
    rows = []
    sid = 1
    for r in adm.itertuples(index=False):
        los = int(np.clip(RNG.normal(9, 4), 1, 28))              # length of stay (days)
        base = adh[r.hospital_id]
        for d in range(los):
            day = pd.Timestamp(r.admit_date) + pd.Timedelta(days=d)
            if day > END:
                break
            # daily KMC hours: adherence scales the WHO-encouraged ~ up-to-16h target
            hours = float(np.clip(RNG.normal(base * 14, 3), 0, 22))
            rows.append({
                "session_id": f"S{sid:06d}",
                "admission_id": r.admission_id,
                "hospital_id": r.hospital_id,
                "session_date": day.date().isoformat(),
                "kmc_hours": round(hours, 1),
                "caregiver_type": RNG.choice(CAREGIVERS, p=CAREGIVER_P),
            })
            sid += 1
    df = pd.DataFrame(rows)
    # duplicate a handful of rows to exercise de-duplication downstream
    dupes = df.sample(15, random_state=1)
    return pd.concat([df, dupes], ignore_index=True)


def make_outcomes(adm: pd.DataFrame, sess: pd.DataFrame) -> pd.DataFrame:
    # average daily KMC per admission drives the (illustrative) outcome model
    avg_kmc = sess.groupby("admission_id")["kmc_hours"].mean()
    rows = []
    for r in adm.itertuples(index=False):
        kmc = avg_kmc.get(r.admission_id, 0.0)
        bw = r.birth_weight_g if not pd.isna(r.birth_weight_g) else 2100
        # lower birthweight + lower KMC -> higher mortality risk (illustrative only)
        risk = 0.14 - 0.006 * kmc - 0.00002 * (bw - 1500)
        risk = float(np.clip(risk, 0.005, 0.25))
        died = RNG.random() < risk
        los = int(np.clip(RNG.normal(9, 4), 1, 30))
        rows.append({
            "admission_id": r.admission_id,
            "discharge_date": (pd.Timestamp(r.admit_date) + pd.Timedelta(days=los)).date().isoformat(),
            "outcome": "Death" if died else RNG.choice(["Discharged", "Referred"], p=[0.93, 0.07]),
            "weight_gain_g_per_kg_day": round(float(np.clip(RNG.normal(kmc * 1.1, 3), -2, 22)), 1),
            "exclusive_breastfeeding": RNG.choice([1, 0], p=[0.8, 0.2]),
            "length_of_stay_days": los,
        })
    return pd.DataFrame(rows)


def main() -> None:
    os.makedirs(RAW_DIR, exist_ok=True)
    adm = make_admissions()
    sess = make_sessions(adm)
    out = make_outcomes(adm, sess)

    pd.DataFrame(
        HOSPITALS,
        columns=["hospital_id", "hospital_name", "district", "state", "sncu_beds", "_base_adherence"],
    ).drop(columns="_base_adherence").to_csv(os.path.join(RAW_DIR, "hospitals.csv"), index=False)

    adm.to_csv(os.path.join(RAW_DIR, "admissions.csv"), index=False)
    sess.to_csv(os.path.join(RAW_DIR, "kmc_sessions.csv"), index=False)
    out.to_csv(os.path.join(RAW_DIR, "outcomes.csv"), index=False)

    print(f"admissions : {len(adm):>6,}")
    print(f"sessions   : {len(sess):>6,}")
    print(f"outcomes   : {len(out):>6,}")
    print(f"written to {RAW_DIR}")


if __name__ == "__main__":
    main()
