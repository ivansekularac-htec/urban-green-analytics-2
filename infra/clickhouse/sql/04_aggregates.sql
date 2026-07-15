-- =============================================================================
-- Creates daily aggregated tables used for dashboard analytics.
-- =============================================================================

USE urbangreen_db;

CREATE TABLE IF NOT EXISTS agg_daily_farm (
    date_key UInt32,
    farm_key UInt64,
    total_harvest_kg Float64,
    harvest_count UInt64,
    premium_harvest_kg Float64,
    non_premium_harvest_kg Float64,
    total_energy_kwh Float64,
    sensor_reading_count UInt64,
    anomaly_count UInt64,
    in_range_count UInt64,
    last_sensor_reading_at DateTime64(3,'UTC'),
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)

)
ENGINE = SummingMergeTree
PARTITION BY intDiv(date_key,100)
ORDER BY (date_key,farm_key);



CREATE TABLE IF NOT EXISTS agg_daily_crop (
    date_key UInt32,
    farm_key UInt64,
    crop_key UInt64,
    total_harvest_kg Float64,
    harvest_count UInt64,
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)

)
ENGINE = SummingMergeTree
PARTITION BY intDiv(date_key,100)
ORDER BY (date_key,farm_key,crop_key);



CREATE TABLE IF NOT EXISTS agg_daily_quality (
    date_key UInt32,
    farm_key UInt64,
    quality_key UInt64,
    total_harvest_kg Float64,
    harvest_count UInt64,
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)

)
ENGINE = SummingMergeTree
PARTITION BY intDiv(date_key,100)
ORDER BY (date_key,farm_key,quality_key);



CREATE TABLE IF NOT EXISTS agg_daily_sensor (
    date_key UInt32,
    farm_key UInt64,
    sensor_key UInt64,
    reading_count UInt64,
    sum_value Float64,
    avg_value Float64,
    min_value Float64,
    max_value Float64,
    anomaly_count UInt64,
    in_range_count UInt64,
    last_reading_at DateTime64(3,'UTC'),
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = SummingMergeTree
PARTITION BY intDiv(date_key,100)
ORDER BY (date_key,farm_key,sensor_key);