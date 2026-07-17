-- Serving grain: one row per farm, crop, and ISO week.

CREATE TABLE IF NOT EXISTS urbangreen.agg_weekly_crop_metrics
(
    week_start_date Date,
    year_week UInt32 MATERIALIZED
        toUInt32(toISOYear(week_start_date) * 100 + toISOWeek(week_start_date)),

    farm_sk UInt64,
    crop_sk UInt64,

    total_yield_kg Decimal(18, 3),
    harvest_count UInt64,

    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(week_start_date)
ORDER BY (farm_sk, crop_sk, week_start_date);
