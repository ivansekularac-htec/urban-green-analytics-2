USE urbangreen_dw;

CREATE TABLE IF NOT EXISTS warehouse_load_state (
    job_name LowCardinality (String),
    cursor_json String,
    last_success_at DateTime64 (3, 'UTC'),
    run_key String,
    _version UInt64
) ENGINE = ReplacingMergeTree (_version)
ORDER BY job_name;