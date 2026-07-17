-- Grain: one row per historical version of a farm (SCD Type 2).

CREATE TABLE IF NOT EXISTS urbangreen.dim_farm
(
    farm_sk UInt64,
    source_farm_id UInt64,

    farm_name String,
    city LowCardinality(String),
    region LowCardinality(String) DEFAULT '',
    farm_status LowCardinality(String),

    size_m2 Decimal(18, 2),
    growing_beds_count UInt32,

    source_infrastructure_type_id Nullable(UInt64),
    infrastructure_type_name LowCardinality(String) DEFAULT '',
    source_growing_system_type_id Nullable(UInt64),
    growing_system_type_name LowCardinality(String) DEFAULT '',

    registered_at Nullable(DateTime64(3, 'UTC')),

    valid_from DateTime64(3, 'UTC'),
    valid_to Nullable(DateTime64(3, 'UTC')),
    is_current UInt8,

    source_updated_at Nullable(DateTime64(3, 'UTC')),
    version_number UInt64,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (source_farm_id, valid_from, farm_sk);
