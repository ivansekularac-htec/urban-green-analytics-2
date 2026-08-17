"""Model-facing Markdown resources for the UrbanGreen warehouse.

This module contains no FastMCP registration. It only builds the text returned
by the schema, metrics, and conventions resources; the MCP server can expose
these functions under stable resource URIs in a later integration ticket.
"""

from functools import lru_cache

from clickhouse_connect.driver.client import Client

from app.clickhouse import get_client

WAREHOUSE_DATABASE = "urbangreen_dw"
INTERNAL_TABLE_PREFIX = ".inner"


def _load_table_ddls(client: Client) -> list[tuple[str, str]]:
    """Return visible warehouse table names and their live ClickHouse DDL."""
    tables_result = client.query(
        """
        SELECT name
        FROM system.tables
        WHERE database = {database:String}
        AND NOT startsWith(name, {internal_prefix:String})
        ORDER BY name
        """,
        parameters={
            "database": WAREHOUSE_DATABASE,
            "internal_prefix": INTERNAL_TABLE_PREFIX,
        },
    )

    # Keep the Python-side guard as a second line of defence. It also protects
    # callers using a ClickHouse version or test double that does not apply the
    # startsWith predicate as expected.
    table_names = [
        row[0] for row in tables_result.result_rows if not row[0].startswith(INTERNAL_TABLE_PREFIX)
    ]

    table_ddls = []
    for table_name in table_names:
        ddl_result = client.query(
            "SHOW CREATE TABLE {database:Identifier}.{table:Identifier}",
            parameters={
                "database": WAREHOUSE_DATABASE,
                "table": table_name,
            },
        )

        if not ddl_result.result_rows:
            raise RuntimeError(
                f"ClickHouse returned no DDL for '{WAREHOUSE_DATABASE}.{table_name}'."
            )

        table_ddls.append((table_name, ddl_result.result_rows[0][0]))

    return table_ddls


def _render_schema_markdown(table_ddls: list[tuple[str, str]]) -> str:
    """Render table names and DDL statements as deterministic Markdown."""
    sections = [
        "# UrbanGreen ClickHouse schema",
        "",
        f"Database: `{WAREHOUSE_DATABASE}`",
        "",
        "The definitions below are read from ClickHouse at runtime. Internal "
        "materialized-view storage tables are omitted.",
    ]

    if not table_ddls:
        sections.extend(["", "No user-visible tables were found."])

    for table_name, ddl in table_ddls:
        sections.extend(
            [
                "",
                f"## `{table_name}`",
                "",
                "```sql",
                ddl.strip(),
                "```",
            ]
        )

    return "\n".join(sections) + "\n"


@lru_cache(maxsize=1)
def get_schema_markdown() -> str:
    """Build the live warehouse schema once, then reuse it for this process."""
    return _render_schema_markdown(_load_table_ddls(get_client()))


METRICS_MARKDOWN = """\
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
"""


def get_metrics_markdown() -> str:
    """Return canonical KPI definitions for the current warehouse design."""
    return METRICS_MARKDOWN


CONVENTIONS_MARKDOWN = """\
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
"""


def get_conventions_markdown() -> str:
    """Return warehouse rules that cannot be inferred reliably from DDL."""
    return CONVENTIONS_MARKDOWN
