# Canonical metric definitions

The metrics the Urban Green dashboards report, with the query each one is
computed from. Use these definitions rather than inventing a variant: two
answers to the same question should be the same number.

All examples read the daily aggregates where possible - they are pre-computed
per farm and day, so they answer in milliseconds where the atomic facts would
scan millions of rows. Each table's `COMMENT` in the schema explains why
`FINAL` appears throughout.

## Yield

### Total harvest yield

Total weight harvested, in kilograms.

```sql
SELECT sum(total_yield_kg) AS total_yield_kg
FROM fact_daily_farm_metrics FINAL
WHERE metric_date BETWEEN {start:Date} AND {end:Date}
```

### Weekly yield trend

The same total grouped by ISO week, for trend charts.

```sql
SELECT d.year_week, sum(m.total_yield_kg) AS total_yield_kg
FROM fact_daily_farm_metrics FINAL m
INNER JOIN dim_date d ON m.date_key = d.date_key
GROUP BY d.year_week
ORDER BY d.year_week
```

### Crop-level yield

Yield per crop. Only the atomic fact carries `crop_id`, so this one does not
use the daily rollup.

```sql
SELECT c.name AS crop, sum(h.weight_kg) AS total_yield_kg
FROM fact_harvests FINAL h
INNER JOIN (SELECT * FROM dim_crop FINAL) c ON h.crop_id = c.crop_id
WHERE h.farm_id = {farm_id:UInt64}
GROUP BY c.name
ORDER BY total_yield_kg DESC
```

### Yield per bed

Yield normalised by the farm's growing capacity, in kg per bed.

```sql
SELECT
    m.farm_id,
    sum(m.total_yield_kg) / any(f.growing_beds_count) AS yield_per_bed_kg
FROM fact_daily_farm_metrics FINAL m
INNER JOIN (SELECT * FROM dim_farm FINAL WHERE is_current = 1) f
    ON m.farm_id = f.farm_id
GROUP BY m.farm_id
```

## Efficiency

### Yield efficiency

Yield per square metre of growing space. Normalises production against farm
size so a large farm is not automatically the best performer.

```sql
SELECT
    m.farm_id,
    sum(m.total_yield_kg) / any(f.size_m2) AS yield_kg_per_m2
FROM fact_daily_farm_metrics FINAL m
INNER JOIN (SELECT * FROM dim_farm FINAL WHERE is_current = 1) f
    ON m.farm_id = f.farm_id
GROUP BY m.farm_id
ORDER BY yield_kg_per_m2 DESC
```

### Energy efficiency

Energy spent per kilogram harvested. Lower is better. Guard the division:
farms with no harvest in the window have no meaningful efficiency.

```sql
SELECT
    farm_id,
    sum(energy_kwh) / nullIf(sum(total_yield_kg), 0) AS kwh_per_kg
FROM fact_daily_farm_metrics FINAL
GROUP BY farm_id
```

### Energy consumption

Raw energy draw, without normalising.

```sql
SELECT sum(energy_kwh) AS energy_kwh
FROM fact_daily_farm_metrics FINAL
WHERE metric_date BETWEEN {start:Date} AND {end:Date}
```

## Quality

### Harvest quality mix

Share of yield by quality grade.

```sql
SELECT
    g.name AS grade,
    sum(q.total_yield_kg) AS total_yield_kg,
    sum(q.total_yield_kg) / sum(sum(q.total_yield_kg)) OVER () AS share
FROM fact_daily_farm_quality_metrics FINAL q
INNER JOIN (SELECT * FROM dim_quality_grade FINAL) g
    ON q.quality_grade_id = g.quality_grade_id
GROUP BY g.name
```

### Premium yield share

Fraction of yield that reached a premium grade.

```sql
SELECT
    sum(premium_yield_kg) / nullIf(sum(total_yield_kg), 0) AS premium_share
FROM fact_daily_farm_metrics FINAL
```

### Waste reduction progress

The complement of the premium share - the portion that did not reach premium
grade. Reported as the waste indicator; the goal is for it to fall.

"Premium" is whichever grades carry `is_premium = 1` on `dim_quality_grade`,
currently grade code A alone. Everything else counts as non-premium, so this
figure covers every grade below premium rather than only the lowest ones. State
that when reporting the number, because a bare percentage is ambiguous.

```sql
SELECT
    sum(non_premium_yield_kg) / nullIf(sum(total_yield_kg), 0) AS non_premium_share
FROM fact_daily_farm_metrics FINAL
```

### Profitability index

Share of yield coming from high-value crop categories. `bi_crop_classification`
is the view that carries the `is_high_value` flag.

```sql
SELECT
    sumIf(h.weight_kg, c.is_high_value = 1) / nullIf(sum(h.weight_kg), 0) AS high_value_share
FROM fact_harvests FINAL h
INNER JOIN bi_crop_classification c ON h.crop_id = c.crop_id
```

## Environment and sensors

### Environmental compliance rate

Share of readings that fell inside the optimal range.

```sql
SELECT
    sum(in_range_count) / nullIf(sum(reading_count), 0) AS compliance_rate
FROM fact_daily_sensor_metrics FINAL
WHERE sensor_type_id = {sensor_type_id:UInt64}
```

### Anomaly rate

The inverse view, for alerting on drift.

```sql
SELECT
    metric_date,
    sum(anomaly_count) / nullIf(sum(reading_count), 0) AS anomaly_rate
FROM fact_daily_sensor_metrics FINAL
GROUP BY metric_date
ORDER BY metric_date
```

### Average sensor value

Sum of sums over sum of counts, never an average of averages.

```sql
SELECT sum(sum_value) / nullIf(sum(reading_count), 0) AS avg_value
FROM fact_daily_sensor_metrics FINAL
WHERE farm_id = {farm_id:UInt64} AND sensor_type_id = {sensor_type_id:UInt64}
```

### Sensor history over time

Daily values per sensor type. Two sources answer this, and they do not return
the same number, so pick deliberately.

The dashboard chart reads the atomic facts and averages the raw readings, which
weights every reading equally:

```sql
SELECT reading_date, sensor_type_id, avg(value) AS avg_value
FROM fact_sensor_readings FINAL
WHERE farm_id = {farm_id:UInt64} AND reading_date >= today() - 7
GROUP BY reading_date, sensor_type_id
ORDER BY reading_date
```

The daily rollup is far cheaper over long ranges, but its per-day value is
already a reading-weighted mean, so averaging those means across days weights
each day equally instead. Divide the sums to stay consistent:

```sql
SELECT metric_date, sensor_type_id,
       sum(sum_value) / nullIf(sum(reading_count), 0) AS avg_value
FROM fact_daily_sensor_metrics FINAL
WHERE farm_id = {farm_id:UInt64}
GROUP BY metric_date, sensor_type_id
ORDER BY metric_date
```

Both are correct daily series and agree whenever every day holds the same
number of readings. To match what the dashboard shows, use the first.

### Light hour compliance

Estimated hours per day the light intensity stayed in range. Light is
`sensor_type_id = 3`.

Derived from the share of readings in range rather than by counting readings,
so it stays correct whatever the sampling interval is:

```sql
SELECT
    metric_date,
    24 * sum(in_range_count) / nullIf(sum(reading_count), 0) AS light_hours_in_range
FROM fact_daily_sensor_metrics FINAL
WHERE farm_id = {farm_id:UInt64} AND sensor_type_id = 3
GROUP BY metric_date
ORDER BY metric_date
```

### Data freshness

Minutes since each farm and sensor type last reported. Compare against
`now64(3, 'UTC')` - readings are stored in UTC, and `now()` in a different
session timezone produces negative ages.

```sql
SELECT
    farm_id,
    sensor_type_id,
    dateDiff('minute', max(reading_ts), now64(3, 'UTC')) AS minutes_since_last_reading
FROM fact_sensor_readings FINAL
GROUP BY farm_id, sensor_type_id
```

## Rankings

### Farm leaderboard

Daily ranking of farms on yield, premium share and energy efficiency, combined
into one score.

```sql
SELECT farm_id, composite_score, composite_rank, yield_rank, quality_rank, energy_rank
FROM fact_farm_leaderboard FINAL
WHERE metric_date = {metric_date:Date}
ORDER BY composite_rank
```

The ranks and the score are computed once per day by the aggregation job. Read
them from this table rather than ranking the farms again: a recomputation over
`fact_daily_farm_metrics` ranks whatever set of farms the query happens to
select, so it disagrees with the dashboard as soon as that set differs.

The recipe is recorded here only so the numbers can be read, not so they can be
rebuilt. On each of the three axes a farm earns `farm_count - axis_rank + 1`
points and the three are summed, which keeps the score comparable across days
with different numbers of competing farms - a plain sum of ranks would not.
`composite_score` is higher-is-better and `composite_rank` 1 is the best farm
that day.

Farms with no yield are placed after every farm with a real efficiency figure
instead of counting as perfectly efficient at zero, and their
`premium_yield_share` is 0.

The table also stores `premium_yield_share` and `energy_efficiency_kwh_per_kg`
per farm and day, so a question about the most efficient farm is answered from
here too.

### Best performing crop

The farm's highest-yielding crop and its yield per square metre.

```sql
SELECT
    c.name AS crop,
    sum(h.weight_kg) / any(f.size_m2) AS kg_per_m2
FROM fact_harvests FINAL h
INNER JOIN (SELECT * FROM dim_crop FINAL) c ON h.crop_id = c.crop_id
INNER JOIN (SELECT * FROM dim_farm FINAL WHERE is_current = 1) f
    ON h.farm_id = f.farm_id
WHERE h.farm_id = {farm_id:UInt64}
GROUP BY c.name
ORDER BY kg_per_m2 DESC
LIMIT 1
```

### City performance

Production compared across cities. `city` lives on the farm dimension.

```sql
SELECT f.city, sum(m.total_yield_kg) AS total_yield_kg
FROM fact_daily_farm_metrics FINAL m
INNER JOIN (SELECT * FROM dim_farm FINAL WHERE is_current = 1) f
    ON m.farm_id = f.farm_id
GROUP BY f.city
ORDER BY total_yield_kg DESC
```
