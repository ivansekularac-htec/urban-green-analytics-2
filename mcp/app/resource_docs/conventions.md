# UrbanGreen ClickHouse Conventions

These rules describe SQL behavior that cannot be inferred reliably from the
schema alone.

## Static dimensions

`dim_date` and `dim_time` use plain `MergeTree`.

Read them normally and do not use `FINAL`.

```sql
SELECT
    date_key,
    full_date
FROM urbangreen_dw.dim_date
```

## Type-1 dimensions

The following Type-1 reference dimensions use
`ReplacingMergeTree(_loaded_at)`:

- `dim_role`
- `dim_quality_grade`
- `dim_crop`
- `dim_user`

When exactly one current row per natural key is required, use `FINAL`:

```sql
SELECT *
FROM urbangreen_dw.dim_crop FINAL
```

or resolve the latest version with `argMax`:

```sql
SELECT
    crop_id,
    argMax(name, _loaded_at) AS name
FROM urbangreen_dw.dim_crop
GROUP BY crop_id
```

Do not assume background merges have already removed older physical versions.

## SCD Type-2 dimensions

The following dimensions preserve history:

- `dim_farm`
- `dim_user_farm_role`
- `dim_sensor`
- `dim_sensor_type`

They use `ReplacingMergeTree(_version)` with
`valid_from`, `valid_to`, and `is_current`.

For current-state queries:

```sql
SELECT *
FROM urbangreen_dw.dim_farm FINAL
WHERE is_current = 1
```

For historical analysis, join the dimension version that was valid at the fact
event timestamp:

```text
event_ts >= valid_from
AND event_ts < valid_to
```

```sql
SELECT
    h.harvest_id,
    f.name AS farm_name
FROM urbangreen_dw.fact_harvests AS h FINAL
INNER JOIN urbangreen_dw.dim_farm AS f FINAL
    ON h.farm_id = f.farm_id
   AND h.harvested_at >= f.valid_from
   AND h.harvested_at < f.valid_to
```

Do not use the current dimension version for historical attributes.

## Fact tables

### Atomic facts

- `fact_harvests` — individual harvest events
- `fact_sensor_readings` — individual sensor readings

Use atomic facts when event-level detail is required.

### Aggregate facts

- `fact_daily_farm_metrics` — daily metrics per farm
- `fact_daily_sensor_metrics` — daily metrics per farm and sensor type
- `fact_daily_farm_quality_metrics` — daily metrics per farm and quality grade
- `fact_farm_leaderboard` — daily farm ranking metrics

Prefer aggregate facts when they already contain the requested daily metric
instead of recomputing it from atomic facts.

### Fact table behavior

All atomic and aggregate fact tables use `ReplacingMergeTree(_loaded_at)` to
support idempotent Spark reloads.

A newer load may replace an existing logical row while an older physical
version remains visible until ClickHouse performs a background merge.

Use `FINAL` when query correctness must not depend on merge timing.

```sql
SELECT
    farm_id,
    sum(weight_kg) AS total_yield_kg
FROM urbangreen_dw.fact_harvests FINAL
GROUP BY farm_id
```
