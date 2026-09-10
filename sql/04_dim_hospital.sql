-- 04_dim_hospital.sql
-- Conformed hospital dimension. Small and slowly-changing; kept as its own model
-- so every fact/mart can join to consistent hospital, district, and state labels.

CREATE OR REPLACE TABLE dim_hospital AS
SELECT
    hospital_id,
    hospital_name,
    district,
    state,
    TRY_CAST(sncu_beds AS INTEGER) AS sncu_beds
FROM raw_hospitals;
