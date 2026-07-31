-- Creates reporting views for executive dashboards.
-- These views expose denormalized datasets consumed by Superset
-- and retain the farm_id column required for Row-Level Security (RLS).

USE urbangreen_dw;

-- Daily farm performance overview.
-- Combines daily farm metrics with farm and calendar dimensions
-- to provide operational KPIs for executive reporting.

CREATE OR REPLACE VIEW vw_exec_overview AS
SELECT
    f.metric_date,
    d.year,
    d.month,
    d.year_week,
    farm.farm_id        AS farm_id,
    farm.name           AS farm_name,
    farm.city           AS city,
    farm.size_m2        AS size_m2,
    f.total_yield_kg        AS total_yield_kg,
    f.harvest_count         AS harvest_count,
    f.premium_yield_kg      AS premium_yield_kg,
    f.non_premium_yield_kg  AS non_premium_yield_kg,
    f.energy_kwh            AS energy_kwh,
    f.reading_count         AS reading_count,
    f.anomaly_count         AS anomaly_count
FROM fact_daily_farm_metrics f
INNER JOIN dim_farm farm
    ON f.farm_key = farm.farm_key
   AND farm.is_current = 1
INNER JOIN dim_date d
    ON f.date_key = d.date_key;

-- Harvest-level reporting view.
-- Combines harvest facts with farm, crop and quality dimensions
-- to support production and quality analysis.

CREATE OR REPLACE VIEW vw_exec_harvest AS
SELECT
    fh.harvest_id          AS harvest_id,
    fh.harvest_date        AS harvest_date,
    fh.harvested_at        AS harvested_at,
    fh.date_key            AS date_key,
    fh.time_key            AS time_key,
    fh.farm_id             AS farm_id,
    f.name                 AS farm_name,
    f.city                 AS city,
    f.size_m2              AS size_m2,
    fh.crop_id             AS crop_id,
    c.name                 AS crop_name,
    c.category_name        AS category_name,
    fh.quality_grade_id    AS quality_grade_id,
    q.code                 AS quality_grade_code,
    q.name                 AS quality_grade_name,
    q.is_premium           AS is_premium,
    fh.weight_kg           AS weight_kg
FROM fact_harvests fh 
INNER JOIN dim_farm f
    ON fh.farm_key = f.farm_key
   AND f.is_current = 1
INNER JOIN dim_crop c
    ON fh.crop_id = c.crop_id
INNER JOIN dim_quality_grade q
    ON fh.quality_grade_id = q.quality_grade_id
INNER JOIN dim_date d
    ON fh.date_key = d.date_key;
