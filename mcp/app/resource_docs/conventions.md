# UrbanGreen ClickHouse query conventions

These rules describe the current warehouse implementation. They take
precedence over assumptions based only on table names or generic star-schema
patterns.

## ReplacingMergeTree facts must be deduplicated

The atomic and aggregate fact tables are rebuilt or refreshed idempotently and
use `ReplacingMergeTree(_loaded_at)`. A replacement row can coexist with its
older physical version until ClickHouse merges the parts. Use `FINAL` when
querying facts so sums and counts do not include both versions.

```sql
SELECT sum(total_yield_kg) AS total_yield_kg
FROM urbangreen_dw.fact_daily_farm_metrics FINAL;
```

The Spark aggregate jobs follow the same rule when they read
`fact_harvests`, `fact_sensor_readings`, and downstream aggregate facts.

## Type-1 reference dimensions use `_loaded_at`

`dim_role`, `dim_quality_grade`, `dim_crop`, and `dim_user` are Type-1
reference dimensions backed by `ReplacingMergeTree(_loaded_at)`. Use `FINAL`
for the current logical row:

```sql
SELECT crop_id, name, category_name
FROM urbangreen_dw.dim_crop FINAL;
```

For a grouped alternative, use `_loaded_at` as the version expression and the
dimension's natural key as the grouping key:

```sql
SELECT
    crop_id,
    argMax(name, _loaded_at) AS name,
    argMax(category_name, _loaded_at) AS category_name
FROM urbangreen_dw.dim_crop
GROUP BY crop_id;
```

## SCD2 dimensions preserve history

`dim_farm`, `dim_user_farm_role`, `dim_sensor`, and `dim_sensor_type` are SCD2
dimensions. They use `_version` to replace a corrected copy of the same
versioned row and use `[valid_from, valid_to)` to describe business validity.

For a current snapshot, deduplicate first and then filter `is_current = 1`:

```sql
SELECT farm_id, name, city, size_m2
FROM urbangreen_dw.dim_farm FINAL
WHERE is_current = 1;
```

For historical attributes, join an event timestamp into the half-open validity
interval rather than attaching today's dimension values:

```sql
SELECT
    h.harvest_id,
    h.harvested_at,
    f.name AS farm_name,
    f.size_m2
FROM urbangreen_dw.fact_harvests AS h FINAL
INNER JOIN urbangreen_dw.dim_farm AS f FINAL
    ON h.farm_id = f.farm_id
   AND h.harvested_at >= f.valid_from
   AND h.harvested_at < f.valid_to;
```

Current dashboards intentionally join aggregate facts to the current farm or
sensor-type row on the natural key and `is_current = 1`.

## Static calendar dimensions do not need `FINAL`

`dim_date` and `dim_time` are generated once and use plain `MergeTree`. Join
them directly:

```sql
SELECT d.year_week, sum(m.total_yield_kg) AS total_yield_kg
FROM urbangreen_dw.fact_daily_farm_metrics AS m FINAL
INNER JOIN urbangreen_dw.dim_date AS d ON m.date_key = d.date_key
GROUP BY d.year_week
ORDER BY d.year_week;
```

## Respect aggregate-table grain

- `fact_daily_farm_metrics`: one row per farm and day.
- `fact_daily_sensor_metrics`: one row per farm, sensor type, and day.
- `fact_daily_farm_quality_metrics`: one row per farm, quality grade, and day.
- `fact_farm_leaderboard`: one row per farm and day.

`farm_key` is carried as a denormalized SCD2 surrogate but is not part of these
business grains. Use `farm_id` when re-aggregating or joining current farm
labels.

```sql
SELECT farm_id, sum(total_yield_kg) AS total_yield_kg
FROM urbangreen_dw.fact_daily_farm_metrics FINAL
GROUP BY farm_id;
```

Do not sum an aggregate fact after joining it to a table that creates multiple
rows per business grain.

## Re-aggregate ratios from their components

Add counts and sums first, then divide. Do not average daily averages or daily
rates because days can contain different numbers of readings.

```sql
SELECT
    sensor_type_id,
    sum(sum_value) / nullIf(sum(reading_count), 0) AS avg_value,
    sum(anomaly_count) / nullIf(sum(reading_count), 0) AS anomaly_rate,
    sum(in_range_count) / nullIf(sum(reading_count), 0) AS compliance_rate
FROM urbangreen_dw.fact_daily_sensor_metrics FINAL
GROUP BY sensor_type_id;
```

Use `nullIf(denominator, 0)` for ratios. A missing denominator is not the same
as a measured zero rate.

## Keep crop value and harvest quality separate

High-value crops and premium quality grades are different classifications.
Use `bi_crop_classification.is_high_value` for the Profitability Index and
`dim_quality_grade.is_premium` for premium-yield metrics.

```sql
SELECT
    sumIf(h.weight_kg, c.is_high_value = 1)
        / nullIf(sum(h.weight_kg), 0) AS profitability_index
FROM urbangreen_dw.fact_harvests AS h FINAL
INNER JOIN urbangreen_dw.bi_crop_classification AS c
    ON h.crop_id = c.crop_id;
```

## Use the timestamp that matches the table grain

- Daily aggregate filtering: `metric_date`.
- Harvest event filtering: `harvested_at` or `harvest_date`.
- Sensor event filtering: `reading_ts` or `reading_date`.
- Warehouse timestamps are stored in UTC.

```sql
SELECT sum(weight_kg) AS todays_yield_kg
FROM urbangreen_dw.fact_harvests FINAL
WHERE harvest_date = today();
```

## Preserve units

- Harvest weight is kilograms.
- Farm area is square metres.
- Aggregate `energy_kwh` is the sum of readings for sensor type
  `Energy Usage`.
- Sensor units and optimal ranges come from the current
  `dim_sensor_type` record.
- Rates are stored and queried as fractions from `0` to `1`; multiply by 100
  only when a percentage value is explicitly required.


## `FINAL` preserves business history

`FINAL` removes older physical copies of rows that share the same
`ReplacingMergeTree` sorting key. It does not remove distinct business events,
metric dates, or SCD2 validity periods.

The warehouse therefore preserves historical business data while returning the
latest corrected version of each row. It does not preserve superseded technical
revisions of the same row; that would require a separate audit log.

For historical ownership or responsibility, do not filter the SCD2 assignment
to `is_current = 1`. Instead, join each event timestamp to the assignment whose
half-open validity interval contains that event:

```sql
SELECT
    ufr.user_id,
    ufr.user_full_name,
    h.farm_id,
    sum(h.weight_kg) AS total_yield_kg
FROM urbangreen_dw.fact_harvests AS h FINAL
INNER JOIN urbangreen_dw.dim_user_farm_role AS ufr FINAL
    ON h.farm_id = ufr.farm_id
   AND h.harvested_at >= ufr.valid_from
   AND h.harvested_at < ufr.valid_to
WHERE ufr.role_name = 'Farm Manager'
  AND ufr.user_id = {manager_id:UInt64}
GROUP BY
    ufr.user_id,
    ufr.user_full_name,
    h.farm_id;
```

Use `fact_harvests.harvested_at` for exact yield attribution and
`fact_sensor_readings.reading_ts` for exact sensor-performance attribution.

Daily aggregate facts can be joined using `metric_date` when manager
assignments change only at day boundaries. If an assignment can change during a
day, use the atomic facts because a single farm-day aggregate cannot be divided
accurately between two managers.
