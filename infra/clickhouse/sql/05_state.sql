USE urbangreen_dw;

CREATE TABLE IF NOT EXISTS warehouse_load_state (
    job_name LowCardinality (String) COMMENT 'Loader job identifier, e.g. load_fact_harvests; one row per job',
    cursor_json String COMMENT 'Incremental load high-water mark for this job, JSON-encoded (e.g. {"updated_at": ...} or {"event_date": ...}); internal ETL bookkeeping, not a business table',
    last_success_at DateTime64 (3, 'UTC'),
    run_key String COMMENT 'Random UUID stamped on each cursor write; identifies which write produced the current row',
    _version UInt64 COMMENT 'ReplacingMergeTree version = load time in milliseconds; higher value always wins for the same job_name'
) ENGINE = ReplacingMergeTree (_version)
ORDER BY job_name;