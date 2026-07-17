-- Grain: one row per historical version of a harvest quality grade.

CREATE TABLE IF NOT EXISTS urbangreen.dim_quality_grade
(
    quality_grade_sk UInt64,
    source_quality_grade_id UInt64,

    quality_grade_code LowCardinality(String),
    quality_grade_name String,
    description String DEFAULT '',

    quality_rank UInt8,
    is_premium UInt8,

    valid_from DateTime64(3, 'UTC'),
    valid_to Nullable(DateTime64(3, 'UTC')),
    is_current UInt8,

    source_updated_at Nullable(DateTime64(3, 'UTC')),
    version_number UInt64,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY (source_quality_grade_id, valid_from, quality_grade_sk);
