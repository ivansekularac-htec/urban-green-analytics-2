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
    harvest_key UInt64 COMMENT 'ETL surrogate key = xxhash64(harvest_id)',
    harvest_id UInt64,
    farm_key UInt64 COMMENT 'SCD2 farm version valid at harvested_at; 0 when the farm dimension row could not be resolved',
    farm_id UInt64,
    crop_id UInt64,
    quality_grade_id UInt64,
    date_key UInt32 COMMENT 'Join key to dim_date',
    time_key UInt32 COMMENT 'Join key to dim_time',
    harvested_at DateTime64 (3, 'UTC'),
    harvest_date Date,
    weight_kg Decimal(10, 3) COMMENT 'Harvested weight in kilograms (kg)',
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (harvest_date)
ORDER BY (
        farm_id, harvest_date, crop_id, harvest_id
    );

CREATE TABLE IF NOT EXISTS fact_sensor_readings (
    reading_key UInt64 COMMENT 'ETL surrogate key = xxhash64(sensor_id, reading_ts)',
    farm_key UInt64 COMMENT 'SCD2 farm version valid at reading_ts; 0 when the farm dimension row could not be resolved',
    farm_id UInt64,
    sensor_id UInt64 COMMENT 'Kafka: farm_sensor_id',
    sensor_type_id UInt64,
    date_key UInt32,
    time_key UInt32,
    reading_ts DateTime64 (3, 'UTC'),
    reading_date Date,
    value Float64 COMMENT 'Measurement value, in the unit of the sensor type version valid at reading_ts (see dim_sensor_type.unit)',
    is_anomaly UInt8 COMMENT 'ETL: 1 when value outside optimal range at reading time',
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (reading_date)
ORDER BY (
        farm_id, sensor_type_id, reading_ts, sensor_id
    );

CREATE TABLE IF NOT EXISTS fact_farm_leaderboard (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64,
    farm_id UInt64,
    total_yield_kg Decimal(18, 3),
    premium_yield_share Float64 COMMENT 'Premium yield / total yield, 0.0-1.0; 0 when total yield is zero',
    energy_efficiency_kwh_per_kg Float64 COMMENT 'Energy use per kg of yield (kWh/kg); lower is better; 0 when total yield is zero',
    yield_rank UInt32 COMMENT 'Daily rank(), 1 = highest total_yield_kg; ties share a rank, next rank has a gap',
    quality_rank UInt32 COMMENT 'Daily rank(), 1 = highest premium_yield_share; ties share a rank, next rank has a gap',
    energy_rank UInt32 COMMENT 'Daily rank(), 1 = most efficient (lowest energy_efficiency_kwh_per_kg); farms with zero yield rank last; ties share a rank, next rank has a gap',
    composite_score Float64 COMMENT 'Sum of (farm_count_that_day - rank + 1) across yield_rank, quality_rank and energy_rank; higher = better',
    composite_rank UInt32 COMMENT 'Daily rank() by composite_score descending; 1 = best farm that day',
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
-- farm_key stays out of the sorting key: it is the SCD2 surrogate
-- (cityHash64(farm_id, valid_from)) and changes on every farm version. The row
-- identity is the business grain (farm per day); a later refresh that stamps a
-- new farm_key must replace the previous row, not sit beside it.
ORDER BY (farm_id, date_key);

CREATE TABLE IF NOT EXISTS fact_daily_farm_metrics (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64 COMMENT 'Denormalized SCD2 surrogate, not part of the farm/day grain',
    farm_id UInt64,
    year_week UInt32 COMMENT 'Denormalized from dim_date for weekly GROUP BY without a join',
    total_yield_kg Decimal(18, 3),
    harvest_count UInt32,
    premium_yield_kg Decimal(18, 3) COMMENT 'Yield from harvests whose quality grade has is_premium = 1',
    non_premium_yield_kg Decimal(18, 3) COMMENT 'Yield from harvests whose quality grade has is_premium = 0',
    energy_kwh Float64 COMMENT 'Sum of readings from the "Energy Usage" sensor type only (kWh); other sensor types are excluded',
    reading_count UInt64,
    anomaly_count UInt64 COMMENT 'Sensor readings that day with is_anomaly = 1',
    in_range_count UInt64 COMMENT 'Sensor readings that day with is_anomaly = 0; compliance rate = in_range_count / reading_count',
    last_sensor_reading_ts Nullable(DateTime64(3, 'UTC')) COMMENT 'Timestamp of the most recent sensor reading rolled into this farm-day',
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
-- farm_key stays out of the sorting key - see fact_farm_leaderboard above.
ORDER BY (farm_id, date_key);

CREATE TABLE IF NOT EXISTS fact_daily_sensor_metrics (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64 COMMENT 'Denormalized SCD2 surrogate, not part of the farm/sensor-type/day grain',
    farm_id UInt64,
    sensor_type_id UInt64,
    reading_count UInt64,
    sum_value Float64 COMMENT 'avg = sum_value / reading_count (re-aggregation safe)',
    min_value Float64 COMMENT 'Minimum reading value that day, in the sensor type unit',
    max_value Float64 COMMENT 'Maximum reading value that day, in the sensor type unit',
    anomaly_count UInt64 COMMENT 'Sensor readings that day with is_anomaly = 1',
    in_range_count UInt64 COMMENT 'Sensor readings that day with is_anomaly = 0; compliance rate = in_range_count / reading_count',
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
-- farm_key stays out of the sorting key - see fact_farm_leaderboard above.
ORDER BY (
        farm_id, date_key, sensor_type_id
    );

CREATE TABLE IF NOT EXISTS fact_daily_farm_quality_metrics (
    metric_date Date,
    date_key UInt32,
    farm_key UInt64 COMMENT 'Denormalized SCD2 surrogate, not part of the farm/quality-grade/day grain',
    farm_id UInt64,
    quality_grade_id UInt64,
    total_yield_kg Decimal(18, 3) COMMENT 'Harvested weight for this farm/day/quality grade, in kg',
    harvest_count UInt32,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
PARTITION BY
    toYYYYMM (metric_date)
-- farm_key stays out of the sorting key - see fact_farm_leaderboard above.
ORDER BY (
        farm_id, date_key, quality_grade_id
    );