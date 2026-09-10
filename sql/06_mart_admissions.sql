-- 06_mart_admissions.sql
-- One wide, analysis-ready row per admission: clinical profile + KMC adherence
-- + outcome, with hospital/state labels joined on. This is the table the
-- dashboard filters and aggregates against.

CREATE OR REPLACE TABLE mart_admissions AS
WITH kmc AS (
    SELECT
        admission_id,
        SUM(kmc_hours_day)                                  AS total_kmc_hours,
        AVG(kmc_hours_day)                                  AS avg_kmc_hours_day,
        SUM(is_adequate_day)                               AS adequate_days,
        COUNT(*)                                            AS days_recorded
    FROM fct_kmc_daily
    GROUP BY admission_id
)
SELECT
    a.admission_id,
    a.hospital_id,
    h.hospital_name,
    h.district,
    h.state,
    a.admit_date,
    DATE_TRUNC('month', a.admit_date)                       AS admit_month,
    a.birth_weight_g,
    a.gestational_age_wks,
    a.sex,
    a.is_lbw,
    a.is_preterm,
    COALESCE(k.avg_kmc_hours_day, 0)                        AS avg_kmc_hours_day,
    COALESCE(k.total_kmc_hours, 0)                          AS total_kmc_hours,
    COALESCE(k.adequate_days, 0)                            AS adequate_days,
    COALESCE(k.days_recorded, 0)                            AS days_recorded,
    -- share of recorded days that met the >=8h adequacy bar
    CASE WHEN k.days_recorded > 0
         THEN ROUND(k.adequate_days * 1.0 / k.days_recorded, 3) END AS adherence_rate,
    o.outcome,
    o.is_death,
    o.weight_gain_g_per_kg_day,
    o.exclusive_breastfeeding,
    o.length_of_stay_days
FROM stg_admissions a
LEFT JOIN dim_hospital  h ON a.hospital_id = h.hospital_id
LEFT JOIN kmc           k ON a.admission_id = k.admission_id
LEFT JOIN stg_outcomes  o ON a.admission_id = o.admission_id;
