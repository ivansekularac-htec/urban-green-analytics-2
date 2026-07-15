USE urbangreen;

CREATE TABLE IF NOT EXISTS agg_daily_farm_harvest
(
    date_key UInt32,
    report_date Date,

    farm_key UInt32,

    total_weight Float32,
    harvest_count UInt32,
    avg_weight Float32,

    loaded_at DateTime
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (farm_key, report_date);

CREATE TABLE IF NOT EXISTS agg_daily_crop_harvest
(
    date_key UInt32,
    report_date Date,

    farm_key UInt32,
    crop_key UInt32,

    total_weight Float32,
    harvest_count UInt32,

    loaded_at DateTime
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (farm_key, crop_key, report_date);

CREATE TABLE IF NOT EXISTS agg_daily_quality
(
    date_key UInt32,
    report_date Date,

    farm_key UInt32,
    quality_grade_key UInt32,

    total_weight Float32,
    harvest_count UInt32,

    loaded_at DateTime
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (farm_key, quality_grade_key, report_date);

CREATE TABLE IF NOT EXISTS agg_daily_sensor
(
    date_key UInt32,
    report_date Date,

    farm_key UInt32,
    sensor_key UInt32,

    avg_value Float32,
    min_value Float32,
    max_value Float32,

    reading_count UInt32,
    anomaly_count UInt32,

    compliance_rate Float32,

    loaded_at DateTime
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (farm_key, sensor_key, report_date);

CREATE TABLE IF NOT EXISTS agg_farm_performance
(
    date_key UInt32,
    report_date Date,

    farm_key UInt32,

    total_yield_kg Float32,

    average_quality_score Float32,

    energy_consumption_kwh Float32,
    energy_efficiency_kwh_kg Float32,

    sensor_anomaly_rate Float32,

    composite_score Float32,

    loaded_at DateTime
)
ENGINE = MergeTree()
PARTITION BY toYYYYMM(report_date)
ORDER BY (farm_key, report_date);
