-- Grain: one row per historical version of a crop.

CREATE TABLE IF NOT EXISTS urbangreen.dim_crop
(
    crop_sk UInt64,
    source_crop_id UInt64,

    crop_name String,
    description String DEFAULT '',

    source_crop_category_id UInt64,
    crop_category_name LowCardinality(String),
    is_high_value UInt8,

    valid_from DateTime64(3, 'UTC'),
    valid_to Nullable(DateTime64(3, 'UTC')),
    is_current UInt8,

    source_updated_at Nullable(DateTime64(3, 'UTC')),
    version_number UInt64,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (source_crop_id, valid_from, crop_sk);
