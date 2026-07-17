-- Serving grain: one row per farm, quality grade, and calendar date.

CREATE TABLE IF NOT EXISTS urbangreen.agg_daily_farm_quality_metrics
(
    metric_date Date,
    date_key UInt32 MATERIALIZED toYYYYMMDD(metric_date),

    farm_sk UInt64,
    quality_grade_sk UInt64,

    total_yield_kg Decimal(18, 3),
    harvest_count UInt64,

    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(metric_date)
ORDER BY (farm_sk, quality_grade_sk, metric_date);
