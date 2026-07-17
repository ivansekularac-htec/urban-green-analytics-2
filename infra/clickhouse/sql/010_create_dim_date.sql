-- Grain: one row per calendar date.
-- Standardizes week, month, quarter, and year groupings.

CREATE TABLE IF NOT EXISTS urbangreen.dim_date
(
    date_key UInt32,
    full_date Date,

    year_number UInt16,
    quarter_number UInt8,

    month_number UInt8,
    month_name LowCardinality(String),

    week_of_year UInt8,
    year_week UInt32,

    day_of_month UInt8,
    day_of_week UInt8,
    day_of_year UInt16,
    day_name LowCardinality(String),

    week_start_date Date,
    month_start_date Date,
    quarter_start_date Date,

    is_weekend UInt8,
    is_month_start UInt8,
    is_month_end UInt8,
    is_quarter_start UInt8,
    is_quarter_end UInt8,
    is_year_start UInt8,
    is_year_end UInt8,

    loaded_at DateTime64(3, 'UTC') DEFAULT now64(3, 'UTC')
)
ENGINE = MergeTree
ORDER BY date_key;
