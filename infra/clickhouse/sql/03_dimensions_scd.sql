-- =============================================================================
-- Urban Green Analytics - ClickHouse warehouse init (3/4)
-- Ticket: T3.1.2 - Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Slowly Changing Dimension (Type 2) tables. Each row is one version of an
--   entity valid in [valid_from, valid_to). Facts carry the natural key plus an
--   event timestamp and resolve the correct version at query time:
--       fact.event_ts >= dim.valid_from AND fact.event_ts < dim.valid_to
--
-- Tables created:
--   dim_farm             - farm attributes over time (status, size_m2, beds)
--   dim_sensor           - sensor status / placement history
--   dim_sensor_type      - optimal_min/max thresholds over time
--   dim_farm_assignment  - user-role-farm assignments over time (bridge, SCD2)
--
-- Surrogate keys:
--   Only here (SCD2) do surrogates make sense, since one natural key has many
--   versions. `*_sk` is a deterministic DEFAULT = cityHash64(natural_key,
--   valid_from), so reloads are idempotent and the version identity is stable.
--   Facts do NOT carry it - they join on the natural key + validity window.
--
-- Version / watermark:
--   ReplacingMergeTree(_version) with ORDER BY (natural_key, valid_from). Because
--   valid_from is in the sorting key, versions are NOT collapsed; only an exact
--   reload of the same version is de-duplicated.
--
-- Design notes:
--   dim_farm_assignment folds the role in (role_name) - no standalone dim_role.
--   farm_id = 0 marks a system-wide role (Postgres NULL farm_id, e.g. Admin).
--   Manager/role history over time (which user held which role on a farm) is
--   answered from dim_farm_assignment, not from attributes on dim_farm.
--
-- Dependencies: 02_dimensions_reference.sql.
-- =============================================================================

USE urbangreen;

CREATE TABLE IF NOT EXISTS dim_farm (
    farm_sk UInt64 DEFAULT cityHash64(farm_id, valid_from),
    farm_id UInt32,
    name String,
    city LowCardinality(String),
    size_m2 Decimal(10, 3),
    growing_beds_count UInt32,
    status LowCardinality(String),
    infrastructure_type_id UInt32,
    infrastructure_type_name LowCardinality(String),
    growing_system_type_id UInt32,
    growing_system_type_name LowCardinality(String),
    valid_from DateTime64(3, 'UTC'),
    valid_to DateTime64(3, 'UTC') DEFAULT toDateTime64('2099-12-31 23:59:59', 3, 'UTC'),
    is_current UInt8,
    _version UInt64
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY (farm_id, valid_from);

CREATE TABLE IF NOT EXISTS dim_sensor (
    sensor_sk UInt64 DEFAULT cityHash64(sensor_id, valid_from),
    sensor_id UInt32,
    farm_id UInt32,
    sensor_type_id UInt32,
    serial_number String,
    status LowCardinality(String),
    installed_at Nullable(DateTime64(3, 'UTC')),
    valid_from DateTime64(3, 'UTC'),
    valid_to DateTime64(3, 'UTC') DEFAULT toDateTime64('2099-12-31 23:59:59', 3, 'UTC'),
    is_current UInt8,
    _version UInt64
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY (sensor_id, valid_from);

CREATE TABLE IF NOT EXISTS dim_sensor_type (
    sensor_type_sk UInt64 DEFAULT cityHash64(sensor_type_id, valid_from),
    sensor_type_id UInt32,
    name LowCardinality(String),
    unit LowCardinality(String),
    description String,
    optimal_min Float64,
    optimal_max Float64,
    valid_from DateTime64(3, 'UTC'),
    valid_to DateTime64(3, 'UTC') DEFAULT toDateTime64('2099-12-31 23:59:59', 3, 'UTC'),
    is_current UInt8,
    _version UInt64
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY (sensor_type_id, valid_from);

CREATE TABLE IF NOT EXISTS dim_farm_assignment (
    assignment_sk UInt64 DEFAULT cityHash64(user_id, role_id, farm_id, valid_from),
    user_id UInt32,
    role_id UInt32,
    role_name LowCardinality(String),
    farm_id UInt32 DEFAULT 0,
    valid_from DateTime64(3, 'UTC'),
    valid_to DateTime64(3, 'UTC') DEFAULT toDateTime64('2099-12-31 23:59:59', 3, 'UTC'),
    is_current UInt8,
    _version UInt64
)
ENGINE = ReplacingMergeTree(_version)
ORDER BY (farm_id, user_id, role_id, valid_from);
