-- Grain: one row per historical version of a sensor-type configuration.

CREATE TABLE IF NOT EXISTS urbangreen.dim_sensor_type
(
    sensor_type_sk UInt64,
    source_sensor_type_id UInt64,

    sensor_type_name LowCardinality(String),
    unit LowCardinality(String),
    description String DEFAULT '',

    optimal_min_value Nullable(Float64),
    optimal_max_value Nullable(Float64),

    measurement_kind LowCardinality(String) DEFAULT 'gauge',
    expected_interval_seconds UInt32 DEFAULT 0,

    valid_from DateTime64(3, 'UTC'),
    valid_to Nullable(DateTime64(3, 'UTC')),
    is_current UInt8,

    source_updated_at Nullable(DateTime64(3, 'UTC')),
    version_number UInt64,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (source_sensor_type_id, valid_from, sensor_type_sk);
