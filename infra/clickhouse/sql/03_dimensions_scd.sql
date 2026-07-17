USE urbangreen_analytics;

CREATE TABLE IF NOT EXISTS dim_farm (
    farm_sk UInt64 DEFAULT cityHash64 (farm_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(farm_id, valid_from)',
    farm_id UInt32,
    name String,
    city LowCardinality (String),
    size_m2 Decimal(10, 3),
    growing_beds_count UInt32,
    status LowCardinality (String),
    infrastructure_type_id UInt32,
    infrastructure_type_name LowCardinality (String),
    growing_system_type_id UInt32,
    growing_system_type_name LowCardinality (String),
    valid_from DateTime64 (3, 'UTC'),
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ),
    is_current UInt8,
    _version UInt64
) ENGINE = ReplacingMergeTree (_version)
ORDER BY (farm_id, valid_from);

CREATE TABLE IF NOT EXISTS dim_user_farm_role (
    user_role_sk UInt64 DEFAULT cityHash64 (user_id, role_id, farm_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(user_id, role_id, farm_id, valid_from)',
    user_role_id UInt32,
    user_id UInt32,
    role_id UInt32,
    farm_id UInt32 DEFAULT 0 COMMENT '0 = system-wide (admin without farm)',
    user_full_name LowCardinality (String),
    role_name LowCardinality (String),
    farm_name LowCardinality (String),
    valid_from DateTime64 (3, 'UTC'),
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ),
    is_current UInt8,
    _version UInt64
) ENGINE = ReplacingMergeTree (_version)
ORDER BY (
        user_id, role_id, farm_id, valid_from
    );

CREATE TABLE IF NOT EXISTS dim_sensor (
    sensor_sk UInt64 DEFAULT cityHash64 (sensor_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(sensor_id, valid_from)',
    sensor_id UInt32,
    farm_id UInt32,
    sensor_type_id UInt32,
    serial_number String,
    status LowCardinality (String),
    installed_at Nullable (DateTime64 (3, 'UTC')),
    valid_from DateTime64 (3, 'UTC'),
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ),
    is_current UInt8,
    _version UInt64
) ENGINE = ReplacingMergeTree (_version)
ORDER BY (sensor_id, valid_from);

CREATE TABLE IF NOT EXISTS dim_sensor_type (
    sensor_type_sk UInt64 DEFAULT cityHash64 (sensor_type_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(sensor_type_id, valid_from)',
    sensor_type_id UInt32,
    name LowCardinality (String),
    unit LowCardinality (String),
    description String,
    optimal_min Float64,
    optimal_max Float64,
    valid_from DateTime64 (3, 'UTC'),
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ),
    is_current UInt8,
    _version UInt64
) ENGINE = ReplacingMergeTree (_version)
ORDER BY (sensor_type_id, valid_from);