# UrbanGreen canonical metrics

These definitions describe the metrics implemented by the current Spark
aggregate jobs and Superset datasets. Unless stated otherwise, ratios are
fractions from `0` to `1`; format them as percentages only at presentation
time. Apply the requested farm and date filters before aggregation.

## Executive Overview

### Total Harvest Yield (kg)

- Meaning: total harvested weight for the selected farms and period.
- Formula: `SUM(total_yield_kg)` from `fact_daily_farm_metrics FINAL`.
- Atomic alternative: `SUM(weight_kg)` from `fact_harvests FINAL` when crop,
  harvest, or quality-level detail is required.

### Yield Efficiency (kg/m²)

- Meaning: harvested weight per square metre for each farm.
- Formula: `SUM(total_yield_kg) / nullIf(MAX(size_m2), 0)`.
- Source: `fact_daily_farm_metrics FINAL` joined to the current `dim_farm`
  record on `farm_id`.
- Grain requirement: group or filter by farm; `MAX(size_m2)` is the current
  area of that farm and is not a portfolio-wide denominator.

### Weekly Yield Trend

- Meaning: total production by calendar week; the current dashboard shows
  weekly totals rather than a calculated week-over-week percentage change.
- Formula: `SUM(total_yield_kg)` grouped into one-week buckets by `metric_date`.
- Source: `fact_daily_farm_metrics FINAL`.

### Harvest Quality Mix (%)

- Meaning: each quality grade's share of harvested weight.
- Formula: grade yield divided by total yield for the selected scope.
- Numerator: `SUM(total_yield_kg)` grouped by quality grade.
- Source: `fact_daily_farm_quality_metrics FINAL` joined to
  `dim_quality_grade FINAL`.

### Profitability Index

- Meaning: share of harvested weight produced by high-value crop categories.
- Formula: `sumIf(weight_kg, is_high_value = 1) / nullIf(SUM(weight_kg), 0)`.
- Source: `fact_harvests FINAL` joined to `bi_crop_classification`.
- High-value classification: the view currently marks `Microgreens` and
  `Specialty Crops` as high value. Do not substitute premium quality grades.

### Farm Expansion Progress

- Meaning: number of currently registered farms against a target of 100.
- Formula: `COUNT(DISTINCT farm_id)` over current `dim_farm` records.
- Current-record rule: read `dim_farm FINAL` with `is_current = 1`.

### Energy Efficiency (kWh/kg)

- Meaning: energy consumed per kilogram harvested.
- Formula: `SUM(energy_kwh) / nullIf(SUM(total_yield_kg), 0)`.
- Source: `fact_daily_farm_metrics FINAL`.
- Zero-yield periods return `NULL` rather than zero efficiency.

### City/Region Performance

- Meaning: harvested weight by farm city.
- Formula: `SUM(total_yield_kg)` grouped by `dim_farm.city`.
- Source: `fact_daily_farm_metrics FINAL` joined to the current `dim_farm`
  record on `farm_id`.

### Top Crop per City

- Meaning: the crop with the greatest total harvested weight in each city.
- Method: aggregate `fact_harvests.weight_kg` by city and crop, then rank
  descending within each city and keep rank `1`.
- Source: `fact_harvests FINAL`, current `dim_farm`, and `dim_crop FINAL`.

## Operations Overview

### Farm Performance Leaderboard

- Grain: one farm per day in `fact_farm_leaderboard FINAL`.
- Yield rank: `total_yield_kg` descending.
- Quality rank: `premium_yield_share` descending, where premium share is
  `premium_yield_kg / total_yield_kg`, or `0` when yield is zero.
- Energy rank: `energy_efficiency_kwh_per_kg` ascending. Farms with no yield
  are placed after farms with a meaningful efficiency value.
- Points per axis: `farm_count - axis_rank + 1`.
- Composite score: the sum of yield, quality, and energy points; higher is
  better.
- Composite rank: composite score descending, with rank `1` representing the
  best-performing farm for that day.
- Current dashboard scope: the most recent date that contains positive yield.

### Live Sensor Anomaly Alerts

- Meaning: individual sensor readings outside the optimal range effective at
  reading time.
- Filter: `is_anomaly = 1` on `fact_sensor_readings FINAL`.
- Display fields include farm, sensor serial number, sensor type, timestamp,
  measured value, unit, and optimal minimum and maximum.
- Apply an explicit `reading_ts` range when "live" must mean a bounded recent
  period; the current chart otherwise follows its selected dashboard range.

### Sensor Anomaly Rate Trend

- Meaning: share of readings marked anomalous, normally shown daily by sensor
  type.
- Formula: `SUM(anomaly_count) / nullIf(SUM(reading_count), 0)`.
- Source: `fact_daily_sensor_metrics FINAL`.
- Current dashboard default: daily values over the last month.

### Sensor Coverage Health Index

- Meaning: share of currently installed sensors whose status is `ACTIVE`.
- Formula: active current sensors divided by all current sensors.
- Source: `dim_sensor FINAL` with `is_current = 1`, grouped by farm.

### Data Freshness Heatmap

- Meaning: minutes elapsed since the most recent reading for each farm and
  sensor type.
- Formula: `dateDiff('minute', MAX(reading_ts), now())`.
- Source: `fact_sensor_readings FINAL`.
- Lower values mean fresher data.

### Environmental Compliance Rate

- Meaning: share of sensor readings inside their configured optimal envelope.
- Formula: `SUM(in_range_count) / nullIf(SUM(reading_count), 0)`.
- Source: `fact_daily_farm_metrics FINAL` for farm-wide compliance or
  `fact_daily_sensor_metrics FINAL` for sensor-type detail.

### Crop Yield by Farm

- Meaning: harvested weight for every farm and crop.
- Formula: `SUM(weight_kg)` grouped by farm and crop.
- Source: `fact_harvests FINAL`, current `dim_farm`, and `dim_crop FINAL` or
  `bi_crop_classification`.

### Harvest Quality Breakdown

- Meaning: harvested weight by farm and quality grade.
- Formula: `SUM(total_yield_kg)` grouped by farm and quality grade.
- Source: `fact_daily_farm_quality_metrics FINAL` joined to current
  `dim_farm` and `dim_quality_grade FINAL`.

### Inactive/Faulty Sensors

- Meaning: current sensors whose status is not `ACTIVE`.
- Formula: count current `dim_sensor` rows where `status != 'ACTIVE'`, grouped
  by farm and sensor type as needed.
- Current-record rule: use `dim_sensor FINAL` with `is_current = 1`.

## Farm Overview

All Farm Overview metrics must be filtered to the selected `farm_id`.

### Live Environmental Gauges

- Meaning: latest observed value for each sensor type on the selected farm.
- Formula: `argMax(value, reading_ts)` grouped by sensor type.
- Source: `fact_sensor_readings FINAL` joined to the current sensor-type
  definition.
- Current gauges cover Temperature, Humidity, Light Intensity, pH Level,
  Energy Usage, and CO2 Concentration.

### Today's Harvest and This Week's Harvest

- Formula: `SUM(weight_kg)` from `fact_harvests FINAL`.
- Today's scope: the current calendar day using `harvested_at`.
- This week's scope: the current calendar week using `harvested_at`.

### Crop-Level Yield

- Meaning: harvested weight by crop for the selected farm.
- Formula: `SUM(weight_kg)` grouped by crop.
- Source: `fact_harvests FINAL` joined to `bi_crop_classification`.

### Best Performing Crop

- Meaning: the crop with the highest harvested kilograms per square metre on
  the selected farm.
- Formula per crop: `SUM(weight_kg) / nullIf(MAX(size_m2), 0)`.
- Area convention: the denominator is the farm's total current area, because
  crop-specific planted area is not stored in the warehouse.
- Rank the result descending and keep the highest value.

### Yield per Bed (kg/bed)

- Meaning: harvested weight per current growing bed for the selected farm.
- Formula: `SUM(total_yield_kg) / nullIf(MAX(growing_beds_count), 0)`.
- Source: `fact_daily_farm_metrics FINAL` joined to current `dim_farm`.

### Harvest Quality Report

- Meaning: quality-grade share of the selected farm's harvested weight.
- Formula: grade yield divided by total farm yield for the selected period.
- Source: `fact_daily_farm_quality_metrics FINAL` joined to
  `dim_quality_grade FINAL`.

### Resource Consumption Trend

- Meaning: daily energy consumption for the selected farm.
- Formula: `SUM(energy_kwh)` grouped by `metric_date`.
- Source: `fact_daily_farm_metrics FINAL`.

### Light Hour Compliance

- Meaning: estimated daily hours during which light readings were inside the
  configured optimal range.
- Formula: `24 * SUM(in_range_count) / nullIf(SUM(reading_count), 0)`.
- Source: `fact_daily_sensor_metrics FINAL`, filtered to sensor type
  `Light Intensity`.
- This is an estimate based on the share of samples in range, not a duration
  reconstructed from irregular event intervals.

### Sensor Data History

- Meaning: historical sensor values for the selected farm.
- Current chart formula: `AVG(value)` grouped by day and sensor type.
- Source: `fact_sensor_readings FINAL`.
- Current dashboard default: the last week.

## Auditor Overview

### Total Energy Consumption (kWh)

- Meaning: total energy readings attributed to the `Energy Usage` sensor type.
- Formula: `SUM(energy_kwh)`.
- Source: `fact_daily_farm_metrics FINAL`.

### Energy Efficiency (kWh/kg)

- Formula: `SUM(energy_kwh) / nullIf(SUM(total_yield_kg), 0)`.
- Source: `fact_daily_farm_metrics FINAL`.

### Waste Reduction Progress (%)

- Current implemented meaning: non-premium harvested weight as a share of all
  harvested weight. Lower values represent less non-premium output.
- Formula: `SUM(non_premium_yield_kg) / nullIf(SUM(total_yield_kg), 0)`.
- Source: `fact_daily_farm_metrics FINAL`.
- Current dashboard default: the last year.

### CO2 Concentration Levels

- Meaning: reading-weighted average CO2 concentration.
- Formula: `SUM(sum_value) / nullIf(SUM(reading_count), 0)`.
- Source: `fact_daily_sensor_metrics FINAL`, filtered to
  `CO2 Concentration`.
- Current dashboard default: daily values over the last week.

### CO2 Compliance Rate

- Meaning: share of CO2 readings inside the configured optimal envelope. The
  current project range is 400–1200 ppm.
- Formula: `SUM(in_range_count) / nullIf(SUM(reading_count), 0)`.
- Source: `fact_daily_sensor_metrics FINAL`, filtered to
  `CO2 Concentration`.
- Current dashboard default: daily values over the last week.
