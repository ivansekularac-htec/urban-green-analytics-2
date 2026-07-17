-- Serving grain: one row per farm and calendar date.
-- Populated later by Module 3/4 processing.

CREATE TABLE IF NOT EXISTS urbangreen.agg_daily_farm_metrics
(
    metric_date Date,
    date_key UInt32 MATERIALIZED toYYYYMMDD(metric_date),
    year_week UInt32 MATERIALIZED
        toUInt32(toISOYear(metric_date) * 100 + toISOWeek(metric_date)),

    farm_sk UInt64,

    total_yield_kg Decimal(18, 3),
    harvest_count UInt64,
    premium_yield_kg Decimal(18, 3),
    non_premium_yield_kg Decimal(18, 3),
    energy_kwh Decimal(18, 6),

    reading_count UInt64,
    anomaly_count UInt64,
    in_range_count UInt64,

    active_sensor_count UInt32,
    total_sensor_count UInt32,

    farm_size_m2_snapshot Decimal(18, 2),
    growing_beds_count_snapshot UInt32,

    first_sensor_reading_timestamp Nullable(DateTime64(3, 'UTC')),
    last_sensor_reading_timestamp Nullable(DateTime64(3, 'UTC')),

    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(metric_date)
ORDER BY (farm_sk, metric_date);
