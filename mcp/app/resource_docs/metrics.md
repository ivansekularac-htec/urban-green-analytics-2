# UrbanGreen canonical metric catalog

These definitions are canonical. Do not invent alternative formulas.

Unless explicitly stated otherwise, ratios return `NULL` when their
denominator is zero or missing. Ratio values are fractions in the range
`0.0` to `1.0`; multiply by `100` only when a percentage value is requested.

## Total harvest yield

Business name: Total Harvest Yield

Unit: kilograms

Source: `urbangreen_dw.fact_daily_farm_metrics`

```sql
SUM(total_yield_kg)
```

## Yield efficiency

Business name: Yield Efficiency

Unit: kilograms per square metre

Sources:

- `urbangreen_dw.fact_daily_farm_metrics`
- Current version of `urbangreen_dw.dim_farm`

Calculate this metric per farm over the selected date range:

```sql
SUM(total_yield_kg) / nullIf(MAX(size_m2), 0)
```

Do not use `AVG(total_yield_kg / size_m2)`.

## Yield per growing bed

Business name: Yield-per-Bed

Unit: kilograms per bed

Sources:

- `urbangreen_dw.fact_daily_farm_metrics`
- Current version of `urbangreen_dw.dim_farm`

```sql
SUM(total_yield_kg) / nullIf(MAX(growing_beds_count), 0)
```

## Energy efficiency

Business name: Energy Efficiency

Unit: kilowatt-hours per kilogram

Source: `urbangreen_dw.fact_daily_farm_metrics`

```sql
SUM(energy_kwh) / nullIf(SUM(total_yield_kg), 0)
```

Lower values indicate better energy efficiency.

This definition applies outside the leaderboard. When reading
`urbangreen_dw.fact_farm_leaderboard`, use the precomputed
`energy_efficiency_kwh_per_kg` value instead of rebuilding it.

## Total energy consumption

Business name: Total Energy Consumption

Unit: kilowatt-hours

Source: `urbangreen_dw.fact_daily_farm_metrics`

```sql
SUM(energy_kwh)
```

## Farm expansion progress

Business name: Farm Expansion Progress

Source: current farms represented in the dashboard dataset

Registered farm count:

```sql
COUNT(DISTINCT farm_id)
```

The dashboard target is `100` farms. Progress against the target is:

```sql
COUNT(DISTINCT farm_id) / 100.0
```

Multiply by `100` only when a percentage value is required.

## Waste reduction progress

Business name: Waste Reduction Progress

Source: `urbangreen_dw.fact_daily_farm_metrics`

The dashboard defines this metric as the non-premium share of harvested
weight:

```sql
SUM(non_premium_yield_kg) / nullIf(SUM(total_yield_kg), 0)
```

Lower values indicate less non-premium output. This is the existing dashboard
definition; it is not a comparison against a historical waste baseline.

## Environmental compliance rate

Business names:

- Environmental Compliance Rate
- Sensor Compliance Rate

Sources:

- `urbangreen_dw.fact_daily_farm_metrics`
- `urbangreen_dw.fact_daily_sensor_metrics`

```sql
SUM(in_range_count) / nullIf(SUM(reading_count), 0)
```

Higher values indicate better compliance.

## Sensor anomaly rate

Business name: Sensor Anomaly Rate

Source: `urbangreen_dw.fact_daily_sensor_metrics`

```sql
SUM(anomaly_count) / nullIf(SUM(reading_count), 0)
```

Lower values indicate fewer anomalous readings.

## Average sensor value

Business name: Average Sensor Value

Source: `urbangreen_dw.fact_daily_sensor_metrics`

```sql
SUM(sum_value) / nullIf(SUM(reading_count), 0)
```

This is a weighted average. Never use:

```sql
AVG(sum_value / reading_count)
```

## Data freshness

Business name: Data Freshness

Unit: minutes since the most recent reading

Source: `urbangreen_dw.fact_sensor_readings`

Calculate freshness per farm and sensor type:

```sql
dateDiff(
    'minute',
    max(reading_ts),
    now()
)
```

Lower values mean fresher data. A missing value means that no sensor reading
exists for the selected farm and sensor type.

## Farm leaderboard

Source: `urbangreen_dw.fact_farm_leaderboard`

Grain: one precomputed row per farm per day.

The following values and ranks are precomputed and must be read from the
leaderboard table rather than rebuilt in an analytical query:

- `total_yield_kg`
- `premium_yield_share`
- `energy_efficiency_kwh_per_kg`
- `yield_rank`
- `quality_rank`
- `energy_rank`
- `composite_score`
- `composite_rank`

The leaderboard is the only exception to the general ratio rule. Its ETL
stores `0` for `premium_yield_share` and `energy_efficiency_kwh_per_kg` when
`total_yield_kg = 0`. This zero is a storage fallback, not a measured
efficiency. Zero-yield farms are explicitly placed after farms with yield when
`energy_rank` is computed. Always read the precomputed leaderboard values and
ranks; do not rank `energy_efficiency_kwh_per_kg` independently.

For each ranking axis, the farm receives:

```text
farm_count - rank + 1
```

The composite score is:

```text
(farm_count - yield_rank + 1)
+ (farm_count - quality_rank + 1)
+ (farm_count - energy_rank + 1)
```

All ranks are computed independently per `metric_date` using `rank()`:

- `yield_rank`: `total_yield_kg` descending.
- `quality_rank`: `premium_yield_share` descending.
- `energy_rank`: farms with yield first, then
  `energy_efficiency_kwh_per_kg` ascending.
- `composite_rank`: `composite_score` descending.

Tied farms receive the same rank and the following rank contains a gap,
matching `rank()` semantics.

`composite_rank = 1` is the highest-ranked farm.
