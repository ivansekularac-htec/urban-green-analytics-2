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
--   A farm's manager history is queried via dim_user_farm_role, not via
--   attributes on dim_farm or dim_user.
--   Surrogate keys (*_key) are deterministic hashes of the version identity
--   (natural key + valid_from), so SCD2 reloads are idempotent and the key is
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
    size_m2 Decimal(10, 3) COMMENT 'Farm growing area in square meters (m²)',
    growing_beds_count UInt32,
    status LowCardinality (String) COMMENT 'Farm lifecycle status as stored in the source system (free-text passthrough, no enum enforced in ETL)',
    infrastructure_type_id UInt64,
    infrastructure_type_name LowCardinality (String) COMMENT 'Denormalized name from farm_infrastructure_types; no separate lookup table is kept',
    growing_system_type_id UInt64,
    growing_system_type_name LowCardinality (String) COMMENT 'Denormalized name from growing_system_types; no separate lookup table is kept',
    valid_from DateTime64 (3, 'UTC') COMMENT 'Inclusive start of this SCD2 version; the first-ever version of an entity opens at 1970-01-01 00:00:00, later versions open at the source change timestamp',
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ) COMMENT 'Exclusive end of this SCD2 version; 2099-12-31 23:59:59 means open/current (see is_current)',
    is_current UInt8 COMMENT '1 = open/current version (valid_to is the far-future sentinel)',
    _version UInt64 COMMENT 'ReplacingMergeTree version = load time in milliseconds; higher value wins for the same natural key + valid_from'
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
    farm_key UInt64 DEFAULT 0 COMMENT '0 = system-wide role or unresolved farm mapping',
    farm_id UInt64 COMMENT '0 = system-wide role (source farm_id is NULL)',
    user_full_name LowCardinality (String),
    role_name LowCardinality (String),
    farm_name LowCardinality (String),
    valid_from DateTime64 (3, 'UTC') COMMENT 'Inclusive start of this SCD2 version; the first-ever version of an entity opens at 1970-01-01 00:00:00, later versions open at the source change timestamp',
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ) COMMENT 'Exclusive end of this SCD2 version; 2099-12-31 23:59:59 means open/current (see is_current)',
    is_current UInt8 COMMENT '1 = open/current version (valid_to is the far-future sentinel)',
    _version UInt64 COMMENT 'ReplacingMergeTree version = load time in milliseconds; higher value wins for the same natural key + valid_from'
) ENGINE = ReplacingMergeTree (_version)
ORDER BY (
        user_role_id, valid_from
    );

CREATE TABLE IF NOT EXISTS dim_sensor (
    sensor_key UInt64 DEFAULT cityHash64 (sensor_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(sensor_id, valid_from)',
    sensor_id UInt64 COMMENT 'Postgres sensors.id; matches Kafka field farm_sensor_id used in fact_sensor_readings.sensor_id',
    farm_id UInt64,
    sensor_type_id UInt64,
    serial_number String,
    status LowCardinality (String) COMMENT 'Sensor lifecycle status as stored in the source system (free-text passthrough, no enum enforced in ETL)',
    installed_at Nullable (DateTime64 (3, 'UTC')) COMMENT 'Physical installation timestamp reported by source; nullable when not yet installed or unknown',
    valid_from DateTime64 (3, 'UTC') COMMENT 'Inclusive start of this SCD2 version; the first-ever version of an entity opens at 1970-01-01 00:00:00, later versions open at the source change timestamp',
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ) COMMENT 'Exclusive end of this SCD2 version; 2099-12-31 23:59:59 means open/current (see is_current)',
    is_current UInt8 COMMENT '1 = open/current version (valid_to is the far-future sentinel)',
    _version UInt64 COMMENT 'ReplacingMergeTree version = load time in milliseconds; higher value wins for the same natural key + valid_from'
) ENGINE = ReplacingMergeTree (_version)
ORDER BY (sensor_id, valid_from);

CREATE TABLE IF NOT EXISTS dim_sensor_type (
    sensor_type_key UInt64 DEFAULT cityHash64 (sensor_type_id, valid_from) COMMENT 'Deterministic SCD2 surrogate = cityHash64(sensor_type_id, valid_from)',
    sensor_type_id UInt64,
    name LowCardinality (String),
    unit LowCardinality (String) COMMENT 'Unit of measurement this sensor type reports in (source-defined, e.g. kWh for the "Energy Usage" type); fact_sensor_readings.value is expressed in this unit',
    description String,
    optimal_min Float64 COMMENT 'Lower anomaly threshold for readings during this SCD2 version',
    optimal_max Float64 COMMENT 'Upper anomaly threshold for readings during this SCD2 version',
    valid_from DateTime64 (3, 'UTC') COMMENT 'Inclusive start of this SCD2 version; the first-ever version of an entity opens at 1970-01-01 00:00:00, later versions open at the source change timestamp',
    valid_to DateTime64 (3, 'UTC') DEFAULT toDateTime64 (
        '2099-12-31 23:59:59',
        3,
        'UTC'
    ) COMMENT 'Exclusive end of this SCD2 version; 2099-12-31 23:59:59 means open/current (see is_current)',
    is_current UInt8 COMMENT '1 = open/current version (valid_to is the far-future sentinel)',
    _version UInt64 COMMENT 'ReplacingMergeTree version = load time in milliseconds; higher value wins for the same natural key + valid_from'
) ENGINE = ReplacingMergeTree (_version)
ORDER BY (sensor_type_id, valid_from);