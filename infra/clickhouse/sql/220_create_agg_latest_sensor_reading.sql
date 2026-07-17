-- Serving grain: one row per physical sensor.

CREATE TABLE IF NOT EXISTS urbangreen.agg_latest_sensor_reading
(
    sensor_sk UInt64,
    farm_sk UInt64,
    sensor_type_sk UInt64,

    latest_reading_timestamp DateTime64(3, 'UTC'),
    latest_sensor_value Float64,

    latest_optimal_min Nullable(Float64),
    latest_optimal_max Nullable(Float64),
    latest_is_in_range Nullable(UInt8),
    latest_anomaly_direction LowCardinality(String) DEFAULT 'unknown',

    kafka_topic LowCardinality(String),
    kafka_partition Int32,
    kafka_offset Int64,

    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = ReplacingMergeTree(latest_reading_timestamp)
ORDER BY sensor_sk;
