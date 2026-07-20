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
--   fact_daily_farm_metrics          — one row per farm per day
--   fact_daily_sensor_metrics        — one row per farm × sensor_type per day
--   fact_daily_farm_quality_metrics  — one row per farm × quality_grade per day
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
USE urbangreen_dw;

CREATE TABLE IF NOT EXISTS fact_harvests (
    harvest_key UInt64,
    harvest_id UInt64,
    farm_key UInt64,
    farm_id UInt64,
    crop_id UInt64,
    quality_grade_id UInt64,
    date_key UInt32,
    time_key UInt32,
    harvested_at DateTime64 (3, 'UTC'),
    harvest_date Date,
    weight_kg Decimal(10, 3),
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (harvest_date)
ORDER BY (
        farm_id, harvest_date, crop_id, harvest_id
    );

CREATE TABLE IF NOT EXISTS fact_sensor_readings (
    reading_key UInt64 COMMENT 'ETL: cityHash64(farm_sensor_id, timestamp)',
    reading_id UInt64 COMMENT 'Kafka: farm_sensor_reading_id',
    farm_key UInt64,
    farm_id UInt64,
    sensor_key UInt64 COMMENT 'Kafka: farm_sensor_id',
    sensor_type_key UInt64,
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
ORDER BY (
        farm_id, sensor_type_key, reading_ts, reading_id
    );

CREATE TABLE IF NOT EXISTS fact_farm_leaderboard (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64,
    farm_id UInt64,
    total_yield_kg Decimal(18, 3),
    premium_yield_share Float64,
    energy_efficiency_kwh_per_kg Float64,
    yield_rank UInt32,
    quality_rank UInt32,
    energy_rank UInt32,
    composite_score Float64,
    composite_rank UInt32,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
ORDER BY (farm_id, date_key, farm_key);

CREATE TABLE IF NOT EXISTS fact_daily_farm_metrics (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64,
    farm_id UInt64,
    year_week UInt32,
    total_yield_kg Decimal(18, 3),
    harvest_count UInt32,
    premium_yield_kg Decimal(18, 3),
    non_premium_yield_kg Decimal(18, 3),
    energy_kwh Float64,
    reading_count UInt64,
    anomaly_count UInt64,
    in_range_count UInt64,
    last_sensor_reading_ts Nullable(DateTime64(3, 'UTC')),
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
ORDER BY (farm_id, date_key, farm_key);

CREATE TABLE IF NOT EXISTS fact_daily_sensor_metrics (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64,
    farm_id UInt64,
    sensor_type_key UInt64,
    reading_count UInt64,
    sum_value Float64 COMMENT 'avg = sum_value / reading_count (re-aggregation safe)',
    min_value Float64,
    max_value Float64,
    anomaly_count UInt64,
    in_range_count UInt64,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
ORDER BY (
        farm_id, date_key, sensor_type_key, farm_key
    );

CREATE TABLE IF NOT EXISTS fact_daily_farm_quality_metrics (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64,
    farm_id UInt64,
    quality_grade_id UInt64,
    total_yield_kg Decimal(18, 3),
    harvest_count UInt32,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
ORDER BY (
        farm_id, date_key, quality_grade_id, farm_key
    );