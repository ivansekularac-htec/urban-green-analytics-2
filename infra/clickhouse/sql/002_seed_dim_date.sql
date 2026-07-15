USE urbangreen;

INSERT INTO dim_date
(
    date_key,
    full_date,
    day,
    week,
    month,
    quarter,
    year,
    is_weekend,
    loaded_at
)
SELECT
    toUInt32(formatDateTime(date, '%Y%m%d')) AS date_key,
    date AS full_date,

    toDayOfMonth(date) AS day,
    toWeek(date) AS week,
    toMonth(date) AS month,
    toQuarter(date) AS quarter,
    toYear(date) AS year,

    dayOfWeek(date) IN (6, 7) AS is_weekend,

    now() AS loaded_at
FROM
(
    SELECT toDate('2020-01-01') + number AS date
    FROM numbers(dateDiff('day', toDate('2020-01-01'), toDate('2036-01-01')))
);