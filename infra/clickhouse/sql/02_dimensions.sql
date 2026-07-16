-- =============================================================================
-- Creates warehouse dimensions and bridge tables.
-- Includes Type 1 dimensions and SCD Type 2 entities.
-- =============================================================================

USE urbangreen_dw;

-- =============================== STATIC DIMENSIONS ===========================

CREATE TABLE IF NOT EXISTS dim_date (
    date_key UInt32,
    full_date Date,
    day UInt8,
    day_of_week UInt8,
    week UInt8,
    month UInt8,
    month_name String,
    quarter UInt8,
    year UInt16,
    is_weekend Bool,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
ORDER BY date_key;


CREATE TABLE IF NOT EXISTS dim_crop (
    crop_key UInt64,
    crop_id UInt64,
    crop_name String,
    category_name String,
    description String,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY crop_id;


CREATE TABLE IF NOT EXISTS dim_quality (
    quality_key UInt64,
    quality_grade_id UInt64,
    code String,
    name String,
    description String,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY quality_grade_id;


CREATE TABLE IF NOT EXISTS dim_user (
    user_key UInt64,
    user_id UInt64,
    email String,
    full_name String,
    is_active Bool,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY user_id;


CREATE TABLE IF NOT EXISTS dim_role (
    role_key UInt64,
    role_id UInt64,
    role_name String,
    description String,
    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY role_id;


-- =============================== USER ROLE BRIDGE ===========================

CREATE TABLE IF NOT EXISTS bridge_user_role (
    user_key UInt64,
    role_key UInt64,
    farm_key UInt64,
    valid_from DateTime64(3,'UTC'),
    valid_to DateTime64(3,'UTC') DEFAULT toDateTime64('2099-12-31 23:59:59',3,'UTC'),
    is_current Bool,
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (user_key, role_key, farm_key, valid_from);


-- =============================== SCD TYPE 2 DIMENSIONS =======================

CREATE TABLE IF NOT EXISTS dim_farm (
    farm_key UInt64,
    farm_id UInt64,
    farm_name String,
    city String,
    infrastructure_type_id UInt64,
    infrastructure_type String,
    growing_system_type_id UInt64,
    growing_system_type String,
    size_m2 Float64,
    beds_count UInt64,
    status String,
    registered_at DateTime64(3,'UTC'),
    valid_from DateTime64(3,'UTC'),
    valid_to DateTime64(3,'UTC') DEFAULT toDateTime64('2099-12-31 23:59:59',3,'UTC'),
    is_current Bool,
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (farm_id, valid_from);



CREATE TABLE IF NOT EXISTS dim_sensor (
    sensor_key UInt64,
    sensor_id UInt64,
    farm_key UInt64,
    sensor_type_id UInt64,
    sensor_type String,
    unit String,
    optimal_min Float64,
    optimal_max Float64,
    serial_number String,
    status String,
    installed_at DateTime64(3,'UTC'),
    valid_from DateTime64(3,'UTC'),
    valid_to DateTime64(3,'UTC') DEFAULT toDateTime64('2099-12-31 23:59:59',3,'UTC'),
    is_current Bool,
    loaded_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(loaded_at)
ORDER BY (sensor_id, valid_from);

