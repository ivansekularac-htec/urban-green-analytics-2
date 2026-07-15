-- =============================================================================
-- Urban Green Analytics - ClickHouse warehouse init (2/4)
-- Ticket: T3.1.2 - Author Star-Schema DDL Init Scripts
-- =============================================================================
--
-- Purpose:
--   Type 1 (reference) dimensions and the conformed date dimension. One current
--   row per natural key - no history is kept, so a plain natural key is enough
--   and no surrogate key is added here (surrogates live only on the SCD2 dims).
--
-- Tables created:
--   dim_date               - generated calendar, seeded in this script
--   dim_crop               - crop + denormalized category (pure star)
--   dim_quality_grade      - A..E grades + is_premium flag
--   dim_user               - users without password_hash (security)
--
-- Version / watermark:
--   Business dims use ReplacingMergeTree(_loaded_at); on merge ClickHouse keeps
--   the row with the greatest _loaded_at per ORDER BY key. Queries that need a
--   guaranteed single row use FINAL or argMax(...).
--
-- Data sources (Module 3 ETL):
--   Postgres app.* -> MinIO Parquet -> Spark -> ClickHouse.
--
-- Dependencies: 01_database.sql.
-- =============================================================================

USE urbangreen;

-- -----------------------------------------------------------------------------
-- dim_date - seeded here so the calendar exists without any ETL run.
-- Range: previous two years plus the current year (2024-01-01 .. 2026-12-31).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key UInt32,
    full_date Date,
    year UInt16,
    quarter UInt8,
    month UInt8,
    month_name LowCardinality(String),
    week UInt8,
    day UInt8,
    day_of_week UInt8,
    day_name LowCardinality(String),
    is_weekend UInt8,
    year_month UInt32,
    year_week UInt32,
    week_start Date,
    month_start Date
)
ENGINE = ReplacingMergeTree()
ORDER BY (date_key);

INSERT INTO dim_date
SELECT
    toUInt32(formatDateTime(d, '%Y%m%d'))            AS date_key,
    d                                                AS full_date,
    toYear(d)                                        AS year,
    toQuarter(d)                                     AS quarter,
    toMonth(d)                                       AS month,
    dateName('month', d)                             AS month_name,
    toISOWeek(d)                                     AS week,
    toDayOfMonth(d)                                  AS day,
    toDayOfWeek(d)                                   AS day_of_week,
    dateName('weekday', d)                           AS day_name,
    toUInt8(toDayOfWeek(d) IN (6, 7))                AS is_weekend,
    toUInt32(toYear(d) * 100 + toMonth(d))           AS year_month,
    toUInt32(toISOYear(d) * 100 + toISOWeek(d))      AS year_week,
    toMonday(d)                                      AS week_start,
    toStartOfMonth(d)                                AS month_start
FROM
(
    SELECT toDate('2024-01-01') + number AS d
    FROM numbers(toUInt32(toDate('2026-12-31') - toDate('2024-01-01') + 1))
);

-- -----------------------------------------------------------------------------
-- dim_crop - crop_category_* denormalized in (star, no snowflake lookup table).
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_crop (
    crop_id UInt32,
    name String,
    description String,
    crop_category_id UInt32,
    crop_category_name LowCardinality(String),
    is_high_value UInt8,
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
ORDER BY (crop_id);

-- -----------------------------------------------------------------------------
-- dim_quality_grade - is_premium supports quality-mix / waste-reduction metrics.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_quality_grade (
    quality_grade_id UInt32,
    code LowCardinality(String),
    name LowCardinality(String),
    description String,
    is_premium UInt8 COMMENT '1 when code = A (Premium), else B-E non-premium',
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
ORDER BY (quality_grade_id);

-- -----------------------------------------------------------------------------
-- dim_user - password_hash intentionally excluded.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_user (
    user_id UInt32,
    email String,
    full_name String,
    is_active UInt8,
    _loaded_at DateTime64(3, 'UTC') DEFAULT now64(3)
)
ENGINE = ReplacingMergeTree(_loaded_at)
ORDER BY (user_id);
