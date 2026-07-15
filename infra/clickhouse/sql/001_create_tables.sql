USE urbangreen;

-- =========================
-- DIM TABLES
-- =========================

CREATE TABLE IF NOT EXISTS dim_date
(
    date_key UInt32I,
    full_date Date,

    day UInt8,
    week UInt8,
    month UInt8,
    quarter UInt8,
    year UInt16,

    is_weekend Bool,
    loaded_at DateTime,
) ENGINE = MergeTree()
ORDER BY(full_date);

CREATE TABLE IF NOT EXISTS quality_grade
(
    quality_grade_key UInt32I,
    quality_grade_id UInt32,

    code String,
    name String,
    description String,

    loaded_at DateTime
) ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY(quality_grade_id);

CREATE TABLE IF NOT EXISTS dim_crop
(
    crop_key UInt32I,
    crop_id UInt32,

    name String,
    description String,

    category_id UInt32,
    category_name String,
    category_description String,

    loaded_at DateTime
) ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY(crop_id);

CREATE TABLE IF NOT EXISTS dim_farm 
(
    farm_key UInt32I,
    farm_id UInt32,

    infrastructure_type_id UInt32,
    infrastructure_type_name String,
    infrastructure_type_description String,

    growing_system_type_id UInt32,
    growing_system_type_name String,
    growing_system_type_description String,

    name String,
    city String,

    size_m2 UInt32,
    status Enum8(
        'ACTIVE' = 1,
        'MAINTENANCE' = 2,
        'INACTIVE' = 3
    ),
    growing_beds_count UInt16,

    valid_from DateTime,
    valid_to DateTime,
    is_current Bool,
    loaded_at DateTime
) ENGINE = MergeTree()
ORDER BY(farm_key);

CREATE TABLE IF NOT EXISTS dim_sensor
(
    sensor_key UInt32I,
    sensor_id UInt32,

    sensor_type_id UInt32,
    sensor_type_name String,
    sensor_type_description String,

    sensor_type_optimal_min Float32,
    sensor_type_optimal_max Float32,

    serial_number String,

    status Enum8(
        'ACTIVE' = 1,
        'OFFLINE' = 2,
        'MAINTENANCE' = 3
    ),
    installed_at DateTime,

    valid_from DateTime,
    valid_to DateTime,
    is_current Bool,
    loaded_at DateTime
) ENGINE = MergeTree()
ORDER BY(sensor_key);

CREATE TABLE IF NOT EXISTS dim_user
(
    user_key UInt32I,
    user_id UInt32,

    email String,
    full_name String,

    is_active Bool,
    loaded_at DateTime
) ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (user_id);

-- =========================
-- FACT TABLES
-- =========================

CREATE TABLE IF NOT EXISTS fact_harvest
(
    harvest_key UInt32,
    harvest_id UInt32,

    date_key UInt32,
    event_date Date,
    timestamp DateTime,

    weight Float32,

    quality_grade_key UInt32,
    crop_key UInt32,
    farm_key UInt32,
    loaded_at DateTime
) ENGINE = MergeTree() -- or ReplacingMergeTree if harvests can be corrected
PARTITION BY toYYYYMM(event_date)
ORDER BY (farm_key, timestamp);

CREATE TABLE IF NOT EXISTS fact_sensor_reading 
(
    sensor_reading_key UInt32,
    sensor_reading_id UInt32,

    date_key UInt32,
    event_date Date,
    timestamp DateTime,

    value Float32,

    sensor_key UInt32,
    farm_key UInt32,
    loaded_at DateTime
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_date)
ORDER BY (sensor_key, timestamp);

-- =========================
-- BRIDGE TABLES
-- =========================

CREATE TABLE IF NOT EXISTS bridge_user_role 
(
    user_key UInt32,
    farm_key UInt32,

    role_id UInt32,
    role_name String,
    role_description String,

    valid_from DateTime,
    valid_to DateTime,
    is_current Bool,
    loaded_at DateTime
) ENGINE = MergeTree()
ORDER BY(user_key, farm_key, role_id);

-- =========================
-- AGG TABLES
-- =========================

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
