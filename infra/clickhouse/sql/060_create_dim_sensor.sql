-- Grain: one row per historical version of a physical farm sensor.

CREATE TABLE IF NOT EXISTS urbangreen.dim_sensor
(
    sensor_sk UInt64,
    source_farm_sensor_id UInt64,

    farm_sk UInt64,
    sensor_type_sk UInt64,

    source_farm_id UInt64,
    source_sensor_type_id UInt64,

    sensor_status LowCardinality(String),
    is_active UInt8,
    installed_at Nullable(DateTime64(3, 'UTC')),

    valid_from DateTime64(3, 'UTC'),
    valid_to Nullable(DateTime64(3, 'UTC')),
    is_current UInt8,

    source_updated_at Nullable(DateTime64(3, 'UTC')),
    version_number UInt64,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (source_farm_sensor_id, valid_from, sensor_sk);
