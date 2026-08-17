# UrbanGreen Metrics

This resource defines the business meaning of metrics used by the UrbanGreen
dashboards.

Column meanings, units, relationships, and table grains are provided by the
live ClickHouse schema.

For calculated ratios, use `nullIf(denominator, 0)` unless a metric explicitly
defines different behavior.

## Shared metric rules

### Premium yield

Premium yield is harvested weight whose quality grade has
`dim_quality_grade.is_premium = 1`.

### Energy usage

Energy metrics use readings from the sensor type named `Energy Usage`.

### Sensor averages

When re-aggregating `urbangreen_dw.fact_daily_sensor_metrics`, calculate the
average from the stored sum and count:

```text
average_value =
    sum(sum_value) / nullIf(sum(reading_count), 0)
```

Do not calculate an average of daily averages.

## Executive Overview

### Total Harvest Yield

Total harvested weight across the selected farms and reporting period.

This represents the overall production output of the UrbanGreen network.

### Yield Efficiency

Harvested production relative to farm area, expressed in kg/m².

```text
yield_efficiency =
    total_yield_kg / nullIf(size_m2, 0)
```

Higher values indicate more production per square metre.

### Weekly Yield Trend

Change in harvested production between reporting weeks.

This metric is used to show whether overall production is increasing,
decreasing, or remaining stable over time.

### Harvest Quality Mix

Distribution of harvested production across quality grades.

It shows how the total harvest is divided between the available quality
categories.

### Profitability Index

Measures the concentration of harvested production in high-value crop
categories.

It indicates how much production comes from crop categories considered more
valuable for the business.

### Farm Expansion Progress

Tracks the number of registered farms against the network target of `100`
farms.

It represents progress toward the planned expansion of the UrbanGreen network.

### Energy Efficiency

Energy consumed relative to harvested production, expressed in kWh/kg.

```text
energy_efficiency_kwh_per_kg =
    energy_kwh / nullIf(total_yield_kg, 0)
```

Lower values indicate less energy consumption per kilogram of harvest.

### City/Region Performance

Harvest production grouped by the city or region of each farm.

This metric is used to compare production performance geographically.

### Top Crop per City

The highest-yielding crop within each city for the selected reporting period.

## Operations Overview

### Farm Performance Leaderboard

Daily comparison of farms across yield, harvest quality, and energy efficiency.

Leaderboard values are precomputed per day in
`urbangreen_dw.fact_farm_leaderboard`.

Use the stored leaderboard values rather than recomputing ranks or scores from
daily metrics.

These include `yield_rank`, `quality_rank`, `energy_rank`,
`composite_score`, and `composite_rank`.

`quality_rank` is based on the precomputed `premium_yield_share`:

```text
premium_yield_share =
    premium_yield_kg / total_yield_kg
```

Higher premium yield share ranks better.

`energy_rank` is based on the precomputed
`energy_efficiency_kwh_per_kg`, where lower energy consumption per kilogram
ranks better for productive farms.

Rank `1` represents the best result.

Spark `rank()` semantics are used: ties receive the same rank and may create
gaps in subsequent ranks.

For the precomputed leaderboard only, farms with zero yield store
`premium_yield_share = 0.0` and `energy_efficiency_kwh_per_kg = 0.0`.

Zero-yield farms are explicitly ranked after farms with positive yield for
energy performance. Do not interpret the stored energy value as perfect
efficiency.

### Live Sensor Anomaly Alerts

Sensor readings whose values are outside the optimal range defined for their
sensor type.

The warehouse identifies these readings through `is_anomaly = 1`.

### Sensor Anomaly Rate Trend

Share of sensor readings classified as anomalous over time.

```text
anomaly_rate =
    anomaly_count / nullIf(reading_count, 0)
```

This is typically analysed by day and sensor type.

### Sensor Coverage Health Index

Share of configured farm sensors that are currently active.

```text
sensor_coverage =
    active_sensor_count / nullIf(total_sensor_count, 0)
```

Higher values indicate better monitoring coverage.

### Data Freshness Heatmap

Shows how recently each farm produced sensor data.

The metric is based on the time elapsed since the latest sensor reading for
each farm. Smaller time gaps indicate fresher data.

### Environmental Compliance Rate

Share of monitored conditions that remain inside the configured optimal range.

```text
compliance_rate =
    in_range_count / nullIf(reading_count, 0)
```

Higher values indicate more stable environmental conditions.

### Crop Yield by Farm

Harvested production grouped by farm and crop.

This metric shows which crops contribute to the output of each farm.

### Harvest Quality Breakdown

Distribution of harvested production across quality grades for each farm.

### Inactive/Faulty Sensors

Number of sensors whose current status indicates that they are inactive or
faulty.

Use the current sensor status rather than inferring sensor health only from
missing readings.

## Farm Overview

Metrics in this section are scoped to the selected farm.

### Live Environmental Gauges

Latest available reading for each sensor type on the farm.

These values represent the farm's current monitored environmental conditions.

### Today's / This Week's Harvest

Total harvested production for the current reporting day or reporting week.

### Crop-Level Yield

Harvested production grouped by crop for the selected farm.

### Best Performing Crop

The crop with the strongest yield performance on the selected farm.

The dashboard also reports its yield efficiency in kg/m².

### Yield-per-Bed

Harvest production relative to the number of growing beds on the farm.

```text
yield_per_bed =
    total_yield_kg / nullIf(growing_beds_count, 0)
```

This allows production to be compared across farms with different numbers of
growing beds.

### Harvest Quality Report

Distribution of the selected farm's harvested production across quality grades.

### Resource Consumption Trend

Energy usage of the selected farm over time.

This metric uses readings from the `Energy Usage` sensor type.

### Light Hour Compliance

Amount of time per day that measured light intensity remains inside the
configured optimal range.

The conversion from sensor readings to compliant hours must follow the
implemented sampling and aggregation logic.

### Sensor Data History

Historical readings for a selected sensor over the requested reporting period.

This represents the detailed time series behind the current and aggregated
sensor metrics.

## Auditor Overview

### Total Energy Consumption

Total energy consumed across the selected farms during the audit period.

This metric uses readings from the `Energy Usage` sensor type.

### Energy Efficiency

Energy consumed per kilogram of harvested production.

```text
energy_efficiency_kwh_per_kg =
    energy_kwh / nullIf(total_yield_kg, 0)
```

This uses the same business definition as the Executive Overview metric.

### Waste Reduction Progress

Non-premium harvested weight as a share of total harvested weight.

```text
waste_reduction_progress =
    non_premium_yield_kg / nullIf(total_yield_kg, 0)
```

Non-premium refers to harvested weight whose quality grade is not marked as
premium.

### CO2 Concentration Levels

Average measured CO2 concentration across the selected farms and reporting
period.

When daily sensor aggregates are used, calculate the average from `sum_value`
and `reading_count` and filter to the CO2 sensor type.

### CO2 Compliance Rate

Share of CO2 readings inside the `400–1200 ppm` compliance range.

```text
co2_compliance_rate =
    compliant_co2_readings / nullIf(total_co2_readings, 0)
```

Only CO2 sensor readings contribute to this metric.