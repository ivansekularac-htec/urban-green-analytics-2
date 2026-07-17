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
