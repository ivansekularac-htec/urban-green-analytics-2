-- =============================================================================
-- Urban Green Analytics — ClickHouse warehouse init (2/4)
-- Ticket: T3.1.2 — Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Type 1 (reference) dimensions and conformed date/time dimensions.
--   Lookups: one current row per natural key (ReplacingMergeTree on _loaded_at).
--   Calendars (dim_date/dim_time): static, generated once, unique by key —
--   plain MergeTree (never reloaded, so no dedup / no FINAL needed on joins).
--
-- Tables created:
--   dim_date, dim_time          — seeded in init (~4k dates, 1440 minute slots)
--   dim_role, dim_quality_grade, dim_crop, dim_user
--
-- Design notes:
--   Pure star: farm/crop reference lookups (infrastructure type, growing system
--   type, crop category) are denormalized directly onto dim_farm / dim_crop
--   (*_name, is_high_value), so no standalone snowflake lookup tables are kept.
--
-- Data sources (Module 3 ETL):
--   Postgres app.* tables → MinIO Parquet (raw/postgres/) → Spark → ClickHouse
--   dim_user excludes password_hash (security).
--
-- Dashboard use:
--   dim_date/dim_time — GROUP BY year_week, month_name, part_of_day without
--   runtime date functions. dim_quality_grade.is_premium, dim_crop.is_high_value
--   support quality mix and profitability metrics.
--
-- Dependencies: 01_database.sql (USE urbangreen_dw).
-- =============================================================================
USE urbangreen_dw;

CREATE TABLE IF NOT EXISTS dim_date (
    date_key UInt32,
    full_date Date,
    year UInt16,
    quarter UInt8,
    month UInt8,
    month_name LowCardinality (String),
    week UInt8,
    day UInt8,
    day_of_week UInt8,
    day_name LowCardinality (String),
    day_of_year UInt16,
    year_month UInt32,
    year_week UInt32,
    week_start Date,
    month_start Date,
    quarter_start Date,
    is_weekend UInt8,
    is_month_start UInt8,
    is_month_end UInt8,
    is_quarter_start UInt8,
    is_quarter_end UInt8,
    is_year_start UInt8,
    is_year_end UInt8
) ENGINE = MergeTree ()
ORDER BY (date_key);

INSERT INTO
    dim_date
SELECT
    toUInt32 (formatDateTime (d, '%Y%m%d')) AS date_key,
    d AS full_date,
    toYear (d) AS year,
    toQuarter (d) AS quarter,
    toMonth (d) AS month,
    dateName ('month', d) AS month_name,
    toISOWeek (d) AS week,
    toDayOfMonth (d) AS day,
    toDayOfWeek (d) AS day_of_week,
    dateName ('weekday', d) AS day_name,
    toDayOfYear (d) AS day_of_year,
    toUInt32 (
        toYear (d) * 100 + toMonth (d)
    ) AS year_month,
    toUInt32 (
        toISOYear (d) * 100 + toISOWeek (d)
    ) AS year_week,
    toMonday (d) AS week_start,
    toStartOfMonth (d) AS month_start,
    toStartOfQuarter (d) AS quarter_start,
    toUInt8 (toDayOfWeek (d) IN (6, 7)) AS is_weekend,
    toUInt8 (d = toStartOfMonth (d)) AS is_month_start,
    toUInt8 (d = toLastDayOfMonth (d)) AS is_month_end,
    toUInt8 (d = toStartOfQuarter (d)) AS is_quarter_start,
    toUInt8 (
        d = toLastDayOfMonth (d)
        AND toMonth (d) IN (3, 6, 9, 12)
    ) AS is_quarter_end,
    toUInt8 (d = toStartOfYear (d)) AS is_year_start,
    toUInt8 (
        toMonth (d) = 12
        AND toDayOfMonth (d) = 31
    ) AS is_year_end
FROM (
        SELECT toDate ('2020-01-01') + number AS d
        FROM numbers (
                toUInt32 (
                    toDate ('2030-12-31') - toDate ('2020-01-01') + 1
                )
            )
    );

CREATE TABLE IF NOT EXISTS dim_time (
    time_key UInt32 COMMENT 'minute grain: hour * 100 + minute',
    hour UInt8,
    minute UInt8,
    quarter_hour_bucket UInt8 COMMENT '0-3, 15-min quarter within the hour',
    part_of_day LowCardinality (String),
    am_pm LowCardinality (String),
    is_business_hours UInt8
) ENGINE = MergeTree ()
ORDER BY (time_key);

INSERT INTO
    dim_time
SELECT
    toUInt32 (h * 100 + m) AS time_key,
    toUInt8 (h) AS hour,
    toUInt8 (m) AS minute,
    toUInt8 (intDiv (m, 15)) AS quarter_hour_bucket,
    multiIf (
        h >= 6
        AND h < 12,
        'Morning',
        h >= 12
        AND h < 18,
        'Afternoon',
        h >= 18
        AND h < 22,
        'Evening',
        'Night'
    ) AS part_of_day,
    if(h < 12, 'AM', 'PM') AS am_pm,
    toUInt8 (h BETWEEN 8 AND 17) AS is_business_hours
FROM (
        SELECT intDiv (number, 60) AS h, number % 60 AS m
        FROM numbers (1440)
    );

CREATE TABLE IF NOT EXISTS dim_role (
    role_key UInt32,
    role_id UInt32,
    name LowCardinality (String),
    description String,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
ORDER BY (role_key);

CREATE TABLE IF NOT EXISTS dim_quality_grade (
    quality_grade_key UInt32,
    quality_grade_id UInt32,
    code LowCardinality (String),
    name LowCardinality (String),
    description String,
    is_premium UInt8 COMMENT '1 when code = A',
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
ORDER BY (quality_grade_key);

CREATE TABLE IF NOT EXISTS dim_crop (
    crop_key UInt32,
    crop_id UInt32,
    name String,
    description String,
    crop_category_id UInt32,
    category_name LowCardinality (String),
    is_high_value UInt8,
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
ORDER BY (crop_key);

CREATE TABLE IF NOT EXISTS dim_user (
    user_key UInt32,
    user_id UInt32,
    email String,
    full_name String,
    is_active UInt8,
    created_at DateTime64 (3, 'UTC'),
    _loaded_at DateTime64 (3, 'UTC') DEFAULT now64 (3)
) ENGINE = ReplacingMergeTree (_loaded_at)
ORDER BY (user_key);