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

-- Farm performance leaderboard.
-- Exposes daily farm rankings across yield, quality,
-- energy efficiency and composite operational performance.
CREATE OR REPLACE VIEW vw_ops_leaderboard AS
SELECT
    l.metric_date AS metric_date,
    l.date_key AS date_key,
    d.year AS year,
    d.month AS month,
    d.year_week AS year_week,
    f.farm_key AS farm_key,
    f.farm_id AS farm_id,
    f.name AS farm_name,
    f.city AS city,
    l.total_yield_kg AS total_yield_kg,
    l.premium_yield_share AS premium_yield_share,
    l.energy_efficiency_kwh_per_kg AS energy_efficiency_kwh_per_kg,
    l.yield_rank AS yield_rank,
    l.quality_rank AS quality_rank,
    l.energy_rank AS energy_rank,
    l.composite_score AS composite_score,
    l.composite_rank AS composite_rank
FROM fact_farm_leaderboard l
INNER JOIN dim_farm f
    ON l.farm_key = f.farm_key
   AND f.is_current = 1
INNER JOIN dim_date d
    ON l.date_key = d.date_key;

-- Sensor monitoring view.
-- Combines sensor readings with farm and sensor metadata,
-- classifying each reading as within or outside the optimal range.
CREATE OR REPLACE VIEW vw_ops_sensor_anomalies AS
SELECT
    sr.reading_ts AS reading_ts,
    sr.reading_date AS metric_date,
    sr.date_key AS date_key,
    d.year AS year,
    d.month AS month,
    d.year_week AS year_week,
    f.farm_key AS farm_key,
    f.farm_id AS farm_id,
    f.name AS farm_name,
    f.city AS city,
    s.sensor_id AS sensor_id,
    s.serial_number AS serial_number,
    s.status AS sensor_status,
    st.sensor_type_id AS sensor_type_id,
    st.name AS sensor_type,
    st.unit AS unit,
    st.optimal_min AS optimal_min,
    st.optimal_max AS optimal_max,
    sr.value AS value,
    multiIf(
        sr.value < st.optimal_min, 'Below minimum',
        sr.value > st.optimal_max, 'Above maximum',
        'Within range'
    ) AS anomaly_reason,
    sr.is_anomaly AS is_anomaly
FROM fact_sensor_readings sr
INNER JOIN dim_sensor s
    ON sr.sensor_key = s.sensor_id
   AND s.is_current = 1
INNER JOIN dim_sensor_type st
    ON sr.sensor_type_key = st.sensor_type_id
    AND st.is_current = 1
INNER JOIN dim_farm f
    ON sr.farm_key = f.farm_key
   AND f.is_current = 1
INNER JOIN dim_date d
    ON sr.date_key = d.date_key;

-- Harvest yield reporting view.
-- Exposes harvest production by farm and crop
-- for operational yield analysis.
CREATE OR REPLACE VIEW vw_ops_crop_yield AS
SELECT
    h.harvest_date AS metric_date,
    h.date_key AS date_key,
    d.year AS year,
    d.month AS month,
    d.year_week AS year_week,
    f.farm_key AS farm_key,
    f.farm_id AS farm_id,
    f.name AS farm_name,
    f.city AS city,
    c.crop_id AS crop_id,
    c.name AS crop_name,
    c.category_name AS category_name,
    h.weight_kg AS weight_kg
FROM fact_harvests h
INNER JOIN dim_farm f
    ON h.farm_key = f.farm_key
   AND f.is_current = 1
INNER JOIN dim_crop c
    ON h.crop_id = c.crop_id
INNER JOIN dim_date d
    ON h.date_key = d.date_key;

-- Daily harvest quality metrics.
-- Provides per-farm production volumes grouped by quality grade
-- for quality monitoring and reporting.
CREATE OR REPLACE VIEW vw_ops_quality AS
SELECT
    q.metric_date AS metric_date,
    q.date_key AS date_key,
    d.year AS year,
    d.month AS month,
    d.year_week AS year_week,
    f.farm_key AS farm_key,
    f.farm_id AS farm_id,
    f.name AS farm_name,
    f.city AS city,
    q.quality_grade_id AS quality_grade_id,
    g.code AS code,
    g.name AS quality_grade,
    g.is_premium AS is_premium,
    q.total_yield_kg AS total_yield_kg,
    q.harvest_count AS harvest_count
FROM fact_daily_farm_quality_metrics q
INNER JOIN dim_quality_grade g
    ON q.quality_grade_id = g.quality_grade_id
INNER JOIN dim_farm f
    ON q.farm_key = f.farm_key
   AND f.is_current = 1
INNER JOIN dim_date d
    ON q.date_key = d.date_key;

-- Daily sensor freshness metrics.
-- Exposes data recency, reading volume, anomaly counts
-- and energy consumption for operational monitoring.
CREATE OR REPLACE VIEW vw_ops_data_freshness AS
SELECT
    m.metric_date AS metric_date,
    m.date_key AS date_key,
    d.year AS year,
    d.month AS month,
    d.year_week AS year_week,
    f.farm_key AS farm_key,
    f.farm_id AS farm_id,
    f.name AS farm_name,
    f.city AS city,
    m.last_sensor_reading_ts AS last_sensor_reading_ts,
    dateDiff(
        'minute',
        m.last_sensor_reading_ts,
        now()
    ) AS minutes_since_last_reading,
    m.reading_count AS reading_count,
    m.anomaly_count AS anomaly_count,
    m.energy_kwh AS energy_kwh
FROM fact_daily_farm_metrics m
INNER JOIN dim_farm f
    ON m.farm_key = f.farm_key
   AND f.is_current = 1
INNER JOIN dim_date d
    ON m.date_key = d.date_key;

-- Sensor inventory view.
-- Lists all active sensors with their farm assignment,
-- status and sensor type metadata.
CREATE OR REPLACE VIEW vw_ops_sensor_inventory AS
SELECT
    f.farm_key AS farm_key,
    f.farm_id AS farm_id,
    f.name AS farm_name,
    f.city AS city,
    s.sensor_id AS sensor_id,
    s.serial_number AS serial_number,
    s.status AS status,
    s.installed_at AS installed_at,
    st.sensor_type_id AS sensor_type_id,
    st.name AS sensor_type
FROM dim_sensor s
INNER JOIN dim_farm f
    ON s.farm_key = f.farm_id
    AND f.is_current = 1
INNER JOIN dim_sensor_type st
    ON s.sensor_type_key = st.sensor_type_id
    AND st.is_current = 1
WHERE s.is_current = 1;