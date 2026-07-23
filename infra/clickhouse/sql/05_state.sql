USE urbangreen_dw;

CREATE TABLE IF NOT EXISTS watermarks (
    job_name LowCardinality (String),
    watermark_value Int64,
    rows_loaded UInt64,
    updated_at DateTime64 (3, 'UTC') DEFAULT now64 (3),
    _version UInt64
) ENGINE = ReplacingMergeTree (_version)
ORDER BY job_name;