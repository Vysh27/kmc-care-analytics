-- 01_stg_admissions.sql
-- Staging layer: clean + standardise raw admission records from the app export.
-- Casts types, derives clinical flags, and screens out impossible weights so the
-- downstream marts only ever see analysis-ready data.
-- (DuckDB TRY_CAST == BigQuery SAFE_CAST; swap the function to port this to BQ.)

CREATE OR REPLACE TABLE stg_admissions AS
SELECT
    admission_id,
    hospital_id,
    CAST(admit_date AS DATE)                       AS admit_date,
    TRY_CAST(birth_weight_g AS INTEGER)            AS birth_weight_g,
    TRY_CAST(gestational_age_wks AS INTEGER)       AS gestational_age_wks,
    UPPER(TRIM(sex))                               AS sex,
    -- clinical flags: low birth weight (<2500g) and preterm (<37 weeks)
    CASE WHEN TRY_CAST(birth_weight_g AS INTEGER) < 2500 THEN TRUE ELSE FALSE END AS is_lbw,
    CASE WHEN TRY_CAST(gestational_age_wks AS INTEGER) < 37 THEN TRUE ELSE FALSE END AS is_preterm,
    -- plausibility flag used by the data-quality model (kept, not dropped, so issues stay visible)
    CASE
        WHEN birth_weight_g IS NULL THEN 'missing_weight'
        WHEN TRY_CAST(birth_weight_g AS INTEGER) < 400
          OR TRY_CAST(birth_weight_g AS INTEGER) > 6000 THEN 'implausible_weight'
        ELSE 'ok'
    END AS weight_quality
FROM raw_admissions;
