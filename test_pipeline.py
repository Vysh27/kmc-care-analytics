"""
Minimal tests for the modeling pipeline. Run with:  python -m pytest -q
(Also runs as a plain script:  python test_pipeline.py)

These guard the properties that matter for trustworthy dashboards: grain,
de-duplication, referential integrity, and value ranges.
"""
from pipeline import build


def _tables():
    return build()


def test_admission_grain_is_unique():
    adm = _tables()["admissions"]
    assert adm["admission_id"].is_unique, "mart_admissions must be one row per admission"


def test_kmc_hours_within_bounds():
    adm = _tables()["admissions"]
    assert adm["avg_kmc_hours_day"].between(0, 24).all(), "KMC hours/day must be 0–24"


def test_no_orphan_hospitals():
    t = _tables()
    valid = set(t["hospitals"]["hospital_id"])
    assert set(t["admissions"]["hospital_id"]).issubset(valid), "every admission maps to a hospital"


def test_data_quality_flags_present():
    dq = _tables()["dq"]
    # the generator injects missing/implausible weights on purpose
    assert len(dq) > 0, "DQ model should catch the injected issues"


if __name__ == "__main__":
    for fn in [
        test_admission_grain_is_unique,
        test_kmc_hours_within_bounds,
        test_no_orphan_hospitals,
        test_data_quality_flags_present,
    ]:
        fn()
        print(f"PASS  {fn.__name__}")
    print("all tests passed")
