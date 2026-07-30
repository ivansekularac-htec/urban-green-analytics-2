USE urbangreen_dw;
-- VIEW

CREATE VIEW IF NOT EXISTS vw_farm_yield_metrics AS

SELECT
    dim_farm.name,
    fact_daily_farm_metrics.metric_date,
    fact_daily_farm_metrics.total_yield_kg,
    dim_farm.size_m2,
    fact_daily_farm_metrics.energy_kwh

FROM fact_daily_farm_metrics

JOIN dim_farm
    ON fact_daily_farm_metrics.farm_key = dim_farm.farm_key;

-- VIEW

CREATE VIEW IF NOT EXISTS vw_weekly_yield_trend AS

SELECT
    fact_daily_farm_metrics.year_week,
    SUM(fact_daily_farm_metrics.total_yield_kg) AS total_yield_kg

FROM fact_daily_farm_metrics

GROUP BY
    fact_daily_farm_metrics.year_week;

-- VIEW

CREATE VIEW IF NOT EXISTS vw_harvest_quality_mix AS

SELECT
    fact_daily_farm_quality_metrics.metric_date,
    dim_quality_grade.code,
    fact_daily_farm_quality_metrics.total_yield_kg

FROM fact_daily_farm_quality_metrics

JOIN dim_quality_grade
    ON fact_daily_farm_quality_metrics.quality_grade_id = dim_quality_grade.quality_grade_id;

-- VIEW

CREATE VIEW IF NOT EXISTS vw_city_crop_performance AS

SELECT
    dim_farm.city,
    dim_crop.name,
    SUM(fact_harvests.weight_kg) AS total_yield_kg

FROM fact_harvests

JOIN dim_farm
    ON fact_harvests.farm_key = dim_farm.farm_key

JOIN dim_crop
    ON fact_harvests.crop_id = dim_crop.crop_id

GROUP BY
    dim_farm.city,
    dim_crop.name;