-- =============================================================================
-- Urban Green Analytics — ClickHouse warehouse init (3/4)
-- Ticket: T3.1.2 — Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Slowly Changing Dimension Type 2 tables. Each row is one version of an
--   entity valid in [valid_from, valid_to). Join facts with:
--     event_ts >= valid_from AND event_ts < valid_to
--
-- Tables created:
--   dim_farm            — farm attributes over time (size_m2, status, beds)
--   dim_user_farm_role  — user–role–farm assignments (bridge-like SCD2)
--   dim_sensor          — sensor status / installation history
--   dim_sensor_type     — optimal_min/max thresholds over time (anomaly logic)
--
-- Design notes:
--   dim_user_farm_role.farm_id = 0 means system-wide role (Postgres NULL).
--   Manager history is queried via dim_user_farm_role,
--   not via attributes on dim_farm or dim_user.
--   Surrogate keys (*_sk) are deterministic hashes of the version identity
--   (natural key + valid_from), so SCD2 reloads are idempotent and the sk is
--   stable for lineage / future equi-joins. ETL may omit it (DEFAULT computes
--   it) or compute the identical value in Spark.
--   Per-farm crop planting history lives in the source (Postgres farm_crops →
--   lake); crop-per-farm metrics are derived from fact_harvests, so no
--   dedicated warehouse dimension is needed.
--
-- Data sources (Module 3 ETL):
--   Postgres → MinIO → Spark (SCD close/open logic on change detection).
--
-- Dependencies: 02_dimensions_reference.sql.
-- =============================================================================
USE urbangreen_dw;

CREATE TABLE IF NOT EXISTS dim_farm (
    farm_key UInt64 DEFAULT cityHash64 (farm_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(farm_id, valid_from)',
    farm_id UInt64,
    name String,
    city LowCardinality (String),
    size_m2 Decimal(10, 3),
    growing_beds_count UInt32,
    status LowCardinality (String),
    infrastructure_type_id UInt64,
    infrastructure_type_name LowCardinality (String),
    growing_system_type_id UInt64,
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
    user_role_key UInt64 DEFAULT cityHash64 (
        user_id,
        role_id,
        farm_id,
        valid_from
    ) COMMENT 'Deterministic SCD2 surrogate = cityHash64(user_id, role_id, farm_id, valid_from)',
    user_role_id UInt64,
    user_id UInt64,
    role_id UInt64,
    farm_key UInt64 DEFAULT 0 COMMENT '0 = system-wide (admin without farm)',
    farm_id UInt64,
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
ORDER BY (user_role_id, valid_from);

CREATE TABLE IF NOT EXISTS dim_sensor (
    sensor_key UInt64 DEFAULT cityHash64 (sensor_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(sensor_id, valid_from)',
    sensor_id UInt64,
    farm_key UInt64,
    sensor_type_key UInt64,
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
    sensor_type_key UInt64 DEFAULT cityHash64 (sensor_type_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(sensor_type_id, valid_from)',
    sensor_type_id UInt64,
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