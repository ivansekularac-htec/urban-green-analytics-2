-- =============================================================================
-- Creates atomic fact tables containing business events and sensor measurements.
-- =============================================================================

USE urbangreen_db;

CREATE TABLE IF NOT EXISTS fact_harvest (
    harvest_key UInt64,
    harvest_id UInt64,
    date_key UInt32,
    farm_key UInt64,
    crop_key UInt64,
    quality_key UInt64,
    weight_kg Float64,
    harvested_at DateTime64(3,'UTC'),
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(harvested_at)
ORDER BY (farm_key, harvested_at, harvest_id);


CREATE TABLE IF NOT EXISTS fact_sensor_reading (
    reading_key UInt64,
    sensor_reading_id UInt64,
    date_key UInt32,
    sensor_key UInt64,
    event_timestamp DateTime64(3,'UTC'),
    value Float64,
    is_anomaly Bool,
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3),

    INDEX idx_anomaly is_anomaly
        TYPE bloom_filter
        GRANULARITY 4
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(event_timestamp)
ORDER BY (sensor_key, event_timestamp, sensor_reading_id);
