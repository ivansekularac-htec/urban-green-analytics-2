"""Markdown knowledge resources for ClickHouse SQL generation."""

from functools import lru_cache

from clickhouse_connect.driver.client import Client

from app.clickhouse import get_client
from app.config import get_settings

_SCHEMA_TABLES_SQL = """
SELECT name
FROM system.tables
WHERE database = {database:String}
  AND NOT startsWith(name, '.inner')
ORDER BY name
"""


def load_schema_markdown(client: Client, database: str) -> str:
    """Introspect ClickHouse and render the warehouse schema as Markdown."""

    result = client.query(
        _SCHEMA_TABLES_SQL,
        parameters={"database": database},
    )

    # Keep the Python-side check as a defensive guard in case ClickHouse ever
    # returns internal materialized-view storage despite the query predicate.
    table_names = [row[0] for row in result.result_rows if not row[0].startswith(".inner")]

    table_ddls = [
        (
            table_name,
            client.command(
                f"SHOW CREATE TABLE {_quote_identifier(database)}.{_quote_identifier(table_name)}"
            ),
        )
        for table_name in table_names
    ]

    return render_schema_markdown(database, table_ddls)


def render_schema_markdown(database: str, table_ddls: list[tuple[str, str]]) -> str:
    """Render already-loaded table DDL as Markdown without external I/O."""

    sections = [
        "# UrbanGreen ClickHouse schema",
        "",
        f"Database: `{database}`",
        "",
    ]

    for table_name, ddl in table_ddls:
        sections.extend(
            [
                f"## `{table_name}`",
                "",
                "```sql",
                ddl.strip(),
                "```",
                "",
            ]
        )

    return "\n".join(sections).rstrip() + "\n"


@lru_cache(maxsize=1)
def schema_resource() -> str:
    """Build the schema lazily and cache it for the process lifetime."""

    settings = get_settings()

    return load_schema_markdown(
        client=get_client(),
        database=settings.clickhouse_db,
    )


def metrics_resource() -> str:
    """Return the canonical warehouse metric definitions."""

    return METRICS_MARKDOWN


def conventions_resource() -> str:
    """Return ClickHouse rules that cannot be inferred from DDL alone."""

    return CONVENTIONS_MARKDOWN


def _quote_identifier(identifier: str) -> str:
    """Quote a ClickHouse database or table identifier."""

    return f"`{identifier.replace('`', '``')}`"


METRICS_MARKDOWN = """\
# UrbanGreen metric definitions

## Daily farm metrics

Source: `fact_daily_farm_metrics`

Grain: one row per farm per day.

- `total_yield_kg`: sum of `fact_harvests.weight_kg`.
- `harvest_count`: number of harvest events.
- `premium_yield_kg`: yield whose quality grade has `is_premium = 1`.
- `non_premium_yield_kg`: yield whose quality grade has `is_premium = 0`.
- `energy_kwh`: sum of sensor values for the `Energy Usage` sensor type.
- `reading_count`: number of sensor readings.
- `anomaly_count`: number of readings where `is_anomaly = 1`.
- `in_range_count`: number of readings where `is_anomaly = 0`.
- `last_sensor_reading_ts`: latest sensor reading timestamp.

## Daily sensor metrics

Source: `fact_daily_sensor_metrics`

Grain: one row per farm and sensor type per day.

- Average sensor value: `sum(sum_value) / sum(reading_count)`.
- Minimum value: `min(min_value)`.
- Maximum value: `max(max_value)`.
- Anomaly rate: `sum(anomaly_count) / sum(reading_count)`.

Never calculate an average using `avg(sum_value / reading_count)` when
combining multiple daily rows. Use the weighted formula above.

## Daily quality metrics

Source: `fact_daily_farm_quality_metrics`

Grain: one row per farm, quality grade, and day.

- `total_yield_kg`: total harvested weight for the quality grade.
- `harvest_count`: number of harvests for the quality grade.

## Farm leaderboard

Source: `fact_farm_leaderboard`

Grain: one row per farm per day.

- Premium yield share: `premium_yield_kg / total_yield_kg`.
- Energy efficiency: `energy_kwh / total_yield_kg`.
- `yield_rank`: descending total yield.
- `quality_rank`: descending premium yield share.
- `energy_rank`: ascending energy consumption per kilogram.
- `composite_score`: sum of points awarded from the three rankings.
- `composite_rank`: descending composite score.

Division by zero must return `0` when `total_yield_kg = 0`.
"""


CONVENTIONS_MARKDOWN = """\
# UrbanGreen ClickHouse conventions

## Type-1 slowly changing dimensions

Type-1 dimensions use `ReplacingMergeTree(_loaded_at)`. ClickHouse may retain
multiple physical versions of the same natural key until background merges
complete, so queries must explicitly select the latest logical row.

Use `FINAL` for straightforward reads:

```sql
SELECT crop_id, name, category_name
FROM dim_crop FINAL;
```

For larger aggregations, use `argMax` with the version timestamp and group by
the natural key:

```sql
SELECT
    crop_id,
    argMax(name, _loaded_at) AS name,
    argMax(category_name, _loaded_at) AS category_name
FROM dim_crop
GROUP BY crop_id;
```

## Type-2 slowly changing dimensions

Type-2 dimensions such as `dim_farm`, `dim_sensor`, `dim_sensor_type`, and
`dim_user_farm_role` preserve history. They use `ReplacingMergeTree(_version)`
with `valid_from`, `valid_to`, and `is_current` columns.

Use `FINAL` before filtering for the current version:

```sql
SELECT farm_id, name, city, status
FROM dim_farm FINAL
WHERE is_current = 1;
```

For historical analysis, deduplicate the dimension first and then join the
event timestamp to the half-open validity interval `[valid_from, valid_to)`:

```sql
WITH farm_history AS (
    SELECT farm_id, name, valid_from, valid_to
    FROM dim_farm FINAL
)
SELECT
    h.harvest_id,
    h.harvested_at,
    f.name AS farm_name
FROM fact_harvests FINAL AS h
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
FROM fact_harvests FINAL
GROUP BY harvest_date
ORDER BY harvest_date;
```
"""
