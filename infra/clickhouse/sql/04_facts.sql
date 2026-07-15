-- =============================================================================
-- Urban Green Analytics - ClickHouse warehouse init (4/4)
-- Ticket: T3.1.2 - Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Fact tables - measurable events at a defined grain. Empty at init; populated
--   by Spark batch jobs (Module 3). Atomic facts carry NATURAL keys + date_key +
--   an event timestamp; SCD2 dimensions are resolved at query time via the
--   validity window, so no surrogate FKs are stored on the atomic facts.
--
-- Atomic facts (one row per event):
--   fact_harvest           - one row per harvest (Postgres harvests -> lake)
--   fact_sensor_reading    - one row per sensor reading (Kafka -> lake)
--
-- Aggregate facts (daily snapshot - dashboard performance):
--   fact_harvest_daily     - one row per farm-version per day
--   fact_sensor_daily      - one row per farm-version x sensor-type-version per day
--
-- Recalculated table (mentor: a table, not a view):
--   fact_farm_leaderboard  - one row per farm-version per snapshot day
--
-- Keys on aggregates (both, on purpose):
--   Aggregates keep BOTH the SCD2 version key (farm_key / sensor_type_key) AND
--   the durable natural id (farm_id / sensor_type_id). The version key lets you
--   attribute performance to a specific state ("did the farm perform better after
--   it moved?"); the natural id gives a trivial continuous entity rollup without
--   a join. The version key is the finer grain and always rolls up to the id.
--
-- Aggregate measures:
--   Additive / re-aggregation-safe only (sum_value + count, min, max, counts),
--   never a pre-computed avg (avg = sum_value / readings_count at query time).
--
-- Engines:
--   ReplacingMergeTree(_loaded_at) everywhere - idempotent hourly reloads.
--
-- Dependencies: 02_dimensions_reference.sql, 03_dimensions_scd.sql.
-- =============================================================================

USE urbangreen;

-- -----------------------------------------------------------------------------
-- fact_harvest - atomic
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_harvest (
    harvest_id UInt64,
    farm_id UInt32,
    crop_id UInt32,
    quality_grade_id UInt32,
    date_key UInt32,
    harvested_at DateTime64(3, 'UTC'),
    harvest_date Date,
    weight_kg Decimal(10, 3),
    is_premium UInt8 COMMENT '1 when quality grade code = A (Premium)',
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
PARTITION BY toYYYYMM(harvest_date)
ORDER BY (farm_id, harvest_date, crop_id, harvest_id);

-- -----------------------------------------------------------------------------
-- fact_sensor_reading - atomic. is_in_range precomputed by ETL against the
-- sensor-type optimal range valid at reading time (1 = inside range).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_sensor_reading (
    reading_id UInt64,
    farm_id UInt32,
    sensor_id UInt32,
    sensor_type_id UInt32,
    date_key UInt32,
    reading_ts DateTime64(3, 'UTC'),
    reading_date Date,
    value Float64,
    is_in_range UInt8,
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
PARTITION BY toYYYYMM(reading_date)
ORDER BY (farm_id, sensor_type_id, reading_ts, reading_id);

-- -----------------------------------------------------------------------------
-- fact_harvest_daily - one row per farm-version per day.
-- Grain keys: farm_id (entity) + farm_key (SCD2 version).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_harvest_daily (
    metric_date Date,
    date_key UInt32,
    farm_id UInt32,
    farm_key UInt64,
    year_week UInt32,
    harvest_count UInt32,
    total_weight_kg Decimal(18, 3),
    min_yield Decimal(10, 3),
    max_yield Decimal(10, 3),
    premium_count UInt32,
    non_premium_count UInt32,
    premium_weight_kg Decimal(18, 3),
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
PARTITION BY toYYYYMM(metric_date)
ORDER BY (farm_id, date_key, farm_key);

-- -----------------------------------------------------------------------------
-- fact_sensor_daily - one row per farm-version x sensor-type-version per day.
-- avg = sum_value / readings_count; anomaly_rate = out_of_range_count / readings.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_sensor_daily (
    metric_date Date,
    date_key UInt32,
    farm_id UInt32,
    farm_key UInt64,
    sensor_type_id UInt32,
    sensor_type_key UInt64,
    readings_count UInt64,
    in_range_count UInt64,
    out_of_range_count UInt64,
    sum_value Float64,
    min_value Float64,
    max_value Float64,
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
PARTITION BY toYYYYMM(metric_date)
ORDER BY (farm_id, sensor_type_id, date_key, farm_key, sensor_type_key);

-- -----------------------------------------------------------------------------
-- fact_farm_leaderboard - recalculated per snapshot day (composite ranking).
-- Grain keys: farm_id (entity) + farm_key (SCD2 version at snapshot time).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_farm_leaderboard (
    snapshot_date Date,
    date_key UInt32,
    farm_id UInt32,
    farm_key UInt64,
    total_yield_kg Decimal(18, 3),
    avg_quality_score Float64,
    energy_per_kg Float64,
    yield_rank UInt32,
    quality_rank UInt32,
    energy_rank UInt32,
    composite_rank UInt32,
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
PARTITION BY toYYYYMM(snapshot_date)
ORDER BY (snapshot_date, farm_id, farm_key);
