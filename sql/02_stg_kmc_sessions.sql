-- 02_stg_kmc_sessions.sql
-- Staging layer for daily KMC (Kangaroo Mother Care) sessions.
-- The app export contains occasional duplicate rows; we de-duplicate on the
-- natural grain (one row per session_id) and clamp obviously invalid hour values.

CREATE OR REPLACE TABLE stg_kmc_sessions AS
WITH deduped AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY session_date) AS rn
    FROM raw_kmc_sessions
)
SELECT
    session_id,
    admission_id,
    hospital_id,
    CAST(session_date AS DATE)                                     AS session_date,
    -- a day has 24 hours; anything above is a logging error -> null it out
    CASE WHEN TRY_CAST(kmc_hours AS DOUBLE) BETWEEN 0 AND 24
         THEN TRY_CAST(kmc_hours AS DOUBLE) END                   AS kmc_hours,
    caregiver_type
FROM deduped
WHERE rn = 1;
