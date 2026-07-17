-- Serving grain: one row per farm, sensor type, and calendar date.

CREATE TABLE IF NOT EXISTS urbangreen.agg_daily_sensor_metrics
(
    metric_date Date,
    date_key UInt32 MATERIALIZED toYYYYMMDD(metric_date),

    farm_sk UInt64,
    sensor_type_sk UInt64,

    reading_count UInt64,
    sum_value Float64,
    average_value Float64,
    minimum_value Float64,
    maximum_value Float64,

    anomaly_count UInt64,
    in_range_count UInt64,

    observed_duration_seconds UInt64,
    in_range_duration_seconds UInt64,
    out_of_range_duration_seconds UInt64,

    first_reading_timestamp Nullable(DateTime64(3, 'UTC')),
    last_reading_timestamp Nullable(DateTime64(3, 'UTC')),

    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(metric_date)
ORDER BY (farm_sk, sensor_type_sk, metric_date);
