USE urbangreen_dw;

-- Helper view that centralizes the high-value crop classification.
CREATE OR REPLACE VIEW bi_crop_classification AS
SELECT
    crop.crop_id,
    crop.name AS crop_name,
    crop.category_name,
    CAST(
        crop.category_name IN (
            'Microgreens',
            'Specialty Crops'
        ),
        'UInt8'
    ) AS is_high_value
FROM dim_crop AS crop FINAL;


-- Supports:
-- - Total Harvest Yield
-- - Yield Efficiency
-- - Profitability Index
-- - Farm Expansion Progress
-- - Energy Efficiency
-- - City Performance
CREATE OR REPLACE VIEW bi_executive_farm_kpis AS
WITH
    harvest_period AS
    (
        SELECT
            min(harvest.harvest_date) AS first_harvest_date,
            max(harvest.harvest_date) AS last_harvest_date
        FROM fact_harvests AS harvest FINAL
    ),

    harvest_by_farm AS
    (
        SELECT
            harvest.farm_id,
            sum(
                toFloat64(harvest.weight_kg)
            ) AS total_yield_kg,
            sumIf(
                toFloat64(harvest.weight_kg),
                ifNull(crop.is_high_value, 0) = 1
        ) AS high_value_yield_kg
        FROM fact_harvests AS harvest
        LEFT JOIN dim_crop AS crop FINAL
            ON harvest.crop_id = crop.crop_id
        GROUP BY harvest.farm_id
        ),

    energy_by_farm AS
    (
        SELECT
            metrics.farm_id,
            sum(metrics.energy_kwh) AS total_energy_kwh
        FROM fact_daily_farm_metrics AS metrics FINAL
        CROSS JOIN harvest_period AS period
        WHERE metrics.metric_date >= period.first_harvest_date
          AND metrics.metric_date <= period.last_harvest_date
        GROUP BY metrics.farm_id
    )

SELECT
    farm.farm_id AS farm_id,
    farm.name AS farm_name,
    farm.city AS city,
    farm.status AS farm_status,
    farm.infrastructure_type_name AS infrastructure_type_name,
    farm.growing_system_type_name AS growing_system_type_name,
    toFloat64(farm.size_m2) AS size_m2,
    ifNull(
        harvest.total_yield_kg,
        0.0
    ) AS total_yield_kg,
    ifNull(
        harvest.high_value_yield_kg,
        0.0
    ) AS high_value_yield_kg,
    ifNull(
        energy.total_energy_kwh,
        0.0
    ) AS total_energy_kwh,
    period.first_harvest_date,
    period.last_harvest_date
FROM dim_farm AS farm FINAL
LEFT JOIN harvest_by_farm AS harvest
    ON farm.farm_id = harvest.farm_id
LEFT JOIN energy_by_farm AS energy
    ON farm.farm_id = energy.farm_id
CROSS JOIN harvest_period AS period
WHERE farm.is_current = 1;


-- Supports:
-- - Weekly Yield Trend
CREATE OR REPLACE VIEW bi_executive_weekly_yield AS
SELECT
    toMonday(metrics.metric_date) AS week_start,
    metrics.farm_id AS farm_id,
    farm.name AS farm_name,
    farm.city AS city,
    sum(
        toFloat64(metrics.total_yield_kg)
    ) AS weekly_yield_kg
FROM fact_daily_farm_metrics AS metrics FINAL
INNER JOIN dim_farm AS farm FINAL
    ON metrics.farm_id = farm.farm_id
WHERE farm.is_current = 1
  AND metrics.total_yield_kg > 0
GROUP BY
    week_start,
    metrics.farm_id,
    farm.name,
    farm.city;


-- Supports:
-- - Harvest Quality Mix
CREATE OR REPLACE VIEW bi_executive_quality_mix AS
SELECT
    quality.metric_date AS metric_date,
    quality.farm_id AS farm_id,
    farm.name AS farm_name,
    farm.city AS city,
    quality.quality_grade_id AS quality_grade_id,
    grade.code AS quality_grade_code,
    grade.name AS quality_grade_name,
    grade.is_premium AS is_premium,
    toFloat64(
        quality.total_yield_kg
    ) AS quality_yield_kg,
    quality.harvest_count AS harvest_count
FROM fact_daily_farm_quality_metrics AS quality FINAL
INNER JOIN dim_farm AS farm FINAL
    ON quality.farm_id = farm.farm_id
INNER JOIN dim_quality_grade AS grade FINAL
    ON quality.quality_grade_id = grade.quality_grade_id
WHERE farm.is_current = 1;
