-- =============================================================================
-- Urban Green Analytics — ClickHouse warehouse init (4/4)
-- Ticket: T3.1.2 — Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Fact tables — measurable events at defined grain. Empty at init; populated
--   by Spark batch jobs (warehouse_load DAG, Module 3).
--
-- Transactional facts (atomic grain):
--   fact_harvests         — one row per harvest (Postgres harvests → lake)
--   fact_sensor_readings  — one row per sensor reading (Kafka → lake)
--     reading_id = cityHash64(farm_sensor_id, timestamp) in ETL
--     sensor_id maps to Kafka field farm_sensor_id
--
-- Aggregate facts (periodic snapshot — dashboard performance):
--   fact_daily_farm_metrics    — one row per farm per day
--   fact_daily_sensor_metrics  — one row per farm × sensor_type per day
--   fact_weekly_crop_metrics   — one row per farm × crop per ISO week
--
-- Engines:
--   ReplacingMergeTree(_loaded_at) — idempotent hourly reloads from lake.
--
-- Lake paths (Module 3):
--   raw/postgres/harvests/          → fact_harvests
--   raw/kafka/sensor_readings/      → fact_sensor_readings
--   Spark rollups after atomic load → fact_daily_* / fact_weekly_*
--
-- Dependencies: 02_dimensions_reference.sql, 03_dimensions_scd.sql.
-- =============================================================================
USE urbangreen_analytics;

CREATE TABLE IF NOT EXISTS fact_harvests (
    harvest_id UInt64,
    farm_id UInt32,
    crop_id UInt32,
    quality_grade_id UInt32,
    date_key UInt32,
    time_key UInt32,
    harvested_at DateTime64 (3, 'UTC'),
    harvest_date Date,
    weight_kg Decimal(10, 3),
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (harvest_date)
ORDER BY (harvest_id);

CREATE TABLE IF NOT EXISTS fact_sensor_readings (
    reading_id UInt64 COMMENT 'ETL: cityHash64(farm_sensor_id, timestamp)',
    farm_id UInt32,
    sensor_id UInt32 COMMENT 'Kafka: farm_sensor_id',
    sensor_type_id UInt32,
    date_key UInt32,
    time_key UInt32,
    reading_ts DateTime64 (3, 'UTC'),
    reading_date Date,
    value Float64,
    is_anomaly UInt8 COMMENT 'ETL: 1 when value outside optimal range at reading time',
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (reading_date)
ORDER BY (reading_id);

CREATE TABLE IF NOT EXISTS fact_daily_farm_metrics (
    metric_date Date,
    date_key UInt32,
    farm_id UInt32,
    year_week UInt32,
    total_yield_kg Decimal(18, 3),
    harvest_count UInt32,
    premium_yield_kg Decimal(18, 3),
    non_premium_yield_kg Decimal(18, 3),
    energy_kwh Float64,
    reading_count UInt64,
    anomaly_count UInt64,
    in_range_count UInt64,
    last_sensor_reading_ts DateTime64 (3, 'UTC'),
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
ORDER BY (farm_id, date_key);

CREATE TABLE IF NOT EXISTS fact_daily_sensor_metrics (
    metric_date Date,
    date_key UInt32,
    farm_id UInt32,
    sensor_type_id UInt32,
    reading_count UInt64,
    sum_value Float64,
    avg_value Float64,
    min_value Float64,
    max_value Float64,
    anomaly_count UInt64,
    in_range_count UInt64,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
ORDER BY (
        farm_id, sensor_type_id, date_key
    );

CREATE TABLE IF NOT EXISTS fact_weekly_crop_metrics (
    year_week UInt32,
    farm_id UInt32,
    crop_id UInt32,
    total_yield_kg Decimal(18, 3),
    harvest_count UInt32,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
ORDER BY (year_week, farm_id, crop_id);