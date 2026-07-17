-- Grain: one row per recorded harvest event.

CREATE TABLE IF NOT EXISTS urbangreen.fact_harvest
(
    harvest_sk UInt64,
    source_harvest_id UInt64,

    farm_sk UInt64,
    crop_sk UInt64,
    quality_grade_sk UInt64,

    harvested_at DateTime64(3, 'UTC'),
    harvest_date Date MATERIALIZED toDate(harvested_at),
    date_key UInt32 MATERIALIZED toYYYYMMDD(harvested_at),

    weight_kg Decimal(18, 3),

    farm_size_m2_snapshot Decimal(18, 2),
    growing_beds_count_snapshot UInt32,

    source_created_at Nullable(DateTime64(3, 'UTC')),
    source_updated_at Nullable(DateTime64(3, 'UTC')),
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(harvest_date)
ORDER BY
(
    harvest_date,
    farm_sk,
    crop_sk,
    quality_grade_sk,
    source_harvest_id
)
SETTINGS index_granularity = 8192;


-- Grain: one row per reading produced by one physical sensor.

CREATE TABLE IF NOT EXISTS urbangreen.fact_sensor_reading
(
    reading_sk UInt64,

    farm_sk UInt64,
    sensor_sk UInt64,
    sensor_type_sk UInt64,

    reading_timestamp DateTime64(3, 'UTC'),
    reading_date Date MATERIALIZED toDate(reading_timestamp),
    date_key UInt32 MATERIALIZED toYYYYMMDD(reading_timestamp),

    sensor_value Float64,

    optimal_min_snapshot Nullable(Float64),
    optimal_max_snapshot Nullable(Float64),

    is_in_range Nullable(UInt8),
    anomaly_direction LowCardinality(String) DEFAULT 'unknown',
    reading_interval_seconds UInt32 DEFAULT 0,

    kafka_topic LowCardinality(String),
    kafka_partition Int32,
    kafka_offset Int64,

    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(reading_date)
ORDER BY
(
    farm_sk,
    sensor_type_sk,
    sensor_sk,
    reading_timestamp,
    kafka_topic,
    kafka_partition,
    kafka_offset
)
SETTINGS index_granularity = 8192;
