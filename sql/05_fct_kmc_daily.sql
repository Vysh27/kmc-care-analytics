-- 05_fct_kmc_daily.sql
-- Fact model at the admission x day grain: total KMC hours delivered per baby per
-- day. This is the core building block for adherence metrics (target is continuous
-- KMC, so daily hours delivered is the operational KPI field teams can act on).

CREATE OR REPLACE TABLE fct_kmc_daily AS
SELECT
    s.admission_id,
    s.hospital_id,
    s.session_date,
    SUM(s.kmc_hours)                     AS kmc_hours_day,
    COUNT(*)                             AS n_sessions,
    -- "adequate" day defined here as >= 8 hours of skin-to-skin contact
    CASE WHEN SUM(s.kmc_hours) >= 8 THEN 1 ELSE 0 END AS is_adequate_day
FROM stg_kmc_sessions s
WHERE s.kmc_hours IS NOT NULL
GROUP BY s.admission_id, s.hospital_id, s.session_date;
