# UrbanGreen Metrics

These are the canonical business rules used by the UrbanGreen Spark warehouse
jobs. Column meanings, units, and table grains are documented in the live
ClickHouse schema.

## Derived metrics

### Premium yield share

Premium yield is determined by quality grades where
`dim_quality_grade.is_premium = 1`.

```text
premium_yield_share =
    premium_yield_kg / total_yield_kg
```

If `total_yield_kg = 0`, the value is `0.0`.

Higher is better.

### Energy efficiency

```text
energy_efficiency_kwh_per_kg =
    energy_kwh / total_yield_kg
```

If `total_yield_kg = 0`, the stored value is `0.0`.

For productive farms, lower energy use per kilogram is better.

For ranking purposes, farms with zero yield are placed after all farms with
positive yield.

### Sensor averages

When re-aggregating `fact_daily_sensor_metrics`, calculate the average as:

```text
average_value =
    sum(sum_value) / nullIf(sum(reading_count), 0)
```

Do not calculate an average of daily averages.

## Leaderboard metrics

Leaderboard metrics are precomputed per day in `fact_farm_leaderboard`.

Use the stored leaderboard values rather than recomputing ranks or scores from
`fact_daily_farm_metrics`.

All leaderboard ranks are calculated independently within each `date_key`.

- `yield_rank` — ranks farms by `total_yield_kg`; higher yield is better.
- `quality_rank` — ranks farms by `premium_yield_share`; higher share is better.
- `energy_rank` — ranks productive farms by `energy_efficiency_kwh_per_kg`;
  lower energy use per kilogram is better. Zero-yield farms rank after
  productive farms.
- `composite_score` — equal-weight score combining yield, quality, and energy
  performance; higher is better.
- `composite_rank` — overall daily leaderboard rank; rank `1` is best.

Spark `rank()` semantics are used: ties receive the same rank and may create
gaps in subsequent ranks.

The absolute `composite_score` depends on the number of farms participating on
that day, so compare it primarily within the same day.