-- 03_stg_outcomes.sql
-- Staging layer for discharge outcomes (one row per admission).

CREATE OR REPLACE TABLE stg_outcomes AS
SELECT
    admission_id,
    CAST(discharge_date AS DATE)                       AS discharge_date,
    outcome,
    CASE WHEN outcome = 'Death' THEN 1 ELSE 0 END      AS is_death,
    TRY_CAST(weight_gain_g_per_kg_day AS DOUBLE)       AS weight_gain_g_per_kg_day,
    TRY_CAST(exclusive_breastfeeding AS INTEGER)       AS exclusive_breastfeeding,
    TRY_CAST(length_of_stay_days AS INTEGER)           AS length_of_stay_days
FROM raw_outcomes;
