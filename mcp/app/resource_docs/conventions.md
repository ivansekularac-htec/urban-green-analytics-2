# UrbanGreen ClickHouse conventions

## Type-1 slowly changing dimensions

Type-1 dimensions use `ReplacingMergeTree(_loaded_at)`. ClickHouse may retain
multiple physical versions of the same natural key until background merges
complete, so queries must explicitly select the latest logical row.

Use `FINAL` for straightforward reads:

```sql
SELECT crop_id, name, category_name
FROM urbangreen_dw.dim_crop FINAL;
```

For larger aggregations, use `argMax` with the version timestamp and group by
the natural key:

```sql
SELECT
    crop_id,
    argMax(name, _loaded_at) AS name,
    argMax(category_name, _loaded_at) AS category_name
FROM urbangreen_dw.dim_crop
GROUP BY crop_id;
```

## Type-2 slowly changing dimensions

Type-2 dimensions such as `urbangreen_dw.dim_farm`,
`urbangreen_dw.dim_sensor`, `urbangreen_dw.dim_sensor_type`, and
`urbangreen_dw.dim_user_farm_role` preserve history. They use
`ReplacingMergeTree(_version)` with `valid_from`, `valid_to`, and `is_current`
columns.

Use `FINAL` before filtering for the current version:

```sql
SELECT farm_id, name, city, status
FROM urbangreen_dw.dim_farm FINAL
WHERE is_current = 1;
```

For historical analysis, deduplicate the dimension first and then join the
event timestamp to the half-open validity interval `[valid_from, valid_to)`:

```sql
WITH farm_history AS (
    SELECT farm_id, name, valid_from, valid_to
    FROM urbangreen_dw.dim_farm FINAL
)
SELECT
    h.harvest_id,
    h.harvested_at,
    f.name AS farm_name
FROM urbangreen_dw.fact_harvests FINAL AS h
INNER JOIN farm_history AS f
    ON h.farm_id = f.farm_id
   AND h.harvested_at >= f.valid_from
   AND h.harvested_at < f.valid_to;
```

## Facts and idempotent reloads

Fact tables represent events or periodic snapshots, but their physical engine
is `ReplacingMergeTree(_loaded_at)` so loaders can replay the same business
grain idempotently. Replacement versions may coexist until background merges
complete. Use `FINAL`, or an equivalent `argMax` deduplication, before an
aggregation that must not double-count replayed rows.

```sql
SELECT
    harvest_date,
    sum(weight_kg) AS total_yield_kg
FROM urbangreen_dw.fact_harvests FINAL
GROUP BY harvest_date
ORDER BY harvest_date;
```
