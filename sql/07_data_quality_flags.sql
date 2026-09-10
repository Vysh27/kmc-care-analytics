-- 07_data_quality_flags.sql
-- Surfaces records that need attention BEFORE numbers reach leadership or
-- government partners. Each row is one flagged issue with a category and detail,
-- so the field/M&E team gets an actionable worklist rather than a silent bad number.

CREATE OR REPLACE TABLE data_quality_flags AS
-- missing or implausible birth weights
SELECT
    admission_id                          AS record_id,
    hospital_id,
    'admissions'                          AS source_table,
    weight_quality                        AS issue,
    CAST(birth_weight_g AS VARCHAR)       AS detail
FROM stg_admissions
WHERE weight_quality <> 'ok'

UNION ALL
-- admissions with no KMC sessions recorded at all
SELECT
    a.admission_id,
    a.hospital_id,
    'kmc_sessions',
    'no_kmc_recorded',
    NULL
FROM stg_admissions a
LEFT JOIN fct_kmc_daily f ON a.admission_id = f.admission_id
WHERE f.admission_id IS NULL

UNION ALL
-- admissions with no outcome recorded
SELECT
    a.admission_id,
    a.hospital_id,
    'outcomes',
    'missing_outcome',
    NULL
FROM stg_admissions a
LEFT JOIN stg_outcomes o ON a.admission_id = o.admission_id
WHERE o.admission_id IS NULL;
