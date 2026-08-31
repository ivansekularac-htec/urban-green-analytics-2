---
name: urbangreen-warehouse
description: Use when answering questions about the UrbanGreen ClickHouse warehouse via the urbangreen-mcp server — farm performance, harvest yield, yield/energy efficiency, sensor readings and compliance, anomaly rates, farm rankings, leaderboard comparisons, and comparisons between farms, cities, crops, or time periods. Enforces canonical KPI formulas, ReplacingMergeTree dedup conventions, precomputed leaderboard values, and sanity-checking of suspicious results before answering.
---

# UrbanGreen Warehouse Querying Skill

## Purpose

Use this skill when answering questions about the UrbanGreen ClickHouse warehouse, including:

- farm performance
- harvest yield
- yield efficiency
- energy consumption or energy efficiency
- sensor readings
- sensor compliance
- anomaly rates
- farm rankings
- leaderboard comparisons
- comparisons between farms, cities, crops, or time periods
- warehouse KPIs and trends

This skill reinforces the correct querying workflow for the `urbangreen-mcp` server and helps prevent incorrect KPI formulas, duplicate counting, unnecessary rank calculations, and misleading interpretations of suspicious data.

---

# Trigger conditions

Apply this skill when a request asks for information from the UrbanGreen warehouse, especially when it involves:

- "best energy efficiency"
- "highest yield"
- "compare two farms"
- "farm performance"
- "sensor compliance"
- "anomaly rate"
- "top farms"
- "leaderboard"
- "yield last month"
- "energy consumption"
- "KPI"
- "trend"
- "warehouse data"

Do not guess table names, columns, KPI formulas, or warehouse conventions from memory when the MCP resources can provide the required information.

---

# Required workflow

Follow this single workflow, in this order, for every warehouse question:

1. **Identify whether a named KPI is involved.** If yes, call `read_warehouse_resource(resource="metrics")` first and use the canonical formula and source table from it. Do not invent alternative formulas.
2. **Discover the schema.**
   - If the relevant table is unknown, call `list_tables`.
   - If the question is broad or exploratory and spans many unfamiliar tables (e.g. "give me an overview of farm performance" with no clear single metric or table), call `read_warehouse_resource(resource="schema")` instead of iterating table-by-table — this is the one case where loading the full schema resource is preferable to targeted discovery.
   - Call `describe_table` for every table that will be used in the SQL. Do not assume column names, types, or table engines — `describe_table` also tells you whether a table is a `ReplacingMergeTree`, which determines whether step 3 applies.
3. **Read conventions if SCD or fact deduplication matters.** Call `read_warehouse_resource(resource="conventions")` before writing SQL against any Type-1 dimension, Type-2 dimension, or `ReplacingMergeTree` fact table — including `fact_farm_leaderboard` (see "Leaderboard table is itself a ReplacingMergeTree fact table" below). Apply the documented `FINAL` or `argMax` deduplication.
4. **Prefer precomputed values.** If the question concerns leaderboard values or ranks, read them directly from `urbangreen_dw.fact_farm_leaderboard` rather than recomputing ranks, scores, or ratios.
5. **Execute one read-only query.** Use `execute_query` with a single SQL statement that answers the question. Do not split one analytical answer across unnecessary separate queries unless additional discovery or validation is required by the steps above.
6. **Sanity-check the result** before presenting it: inspect zeros, missing values, ties, and any of the known data quirks below.
7. **Answer the user**, clearly distinguishing measured performance from suspicious or missing-data artifacts.

---

# Schema and deduplication rules

## Type-1 slowly changing dimensions

Type-1 dimensions use:

```text
ReplacingMergeTree(_loaded_at)
```

ClickHouse may retain multiple physical versions of the same natural key until background merges complete.

For straightforward reads, use:

```sql
SELECT crop_id, name, category_name
FROM urbangreen_dw.dim_crop FINAL;
```

For larger aggregations, use `argMax` with the version timestamp and group by the natural key:

```sql
SELECT
    crop_id,
    argMax(name, _loaded_at) AS name,
    argMax(category_name, _loaded_at) AS category_name
FROM urbangreen_dw.dim_crop
GROUP BY crop_id;
```

---

## Type-2 slowly changing dimensions

Type-2 dimensions include:

* `urbangreen_dw.dim_farm`
* `urbangreen_dw.dim_sensor`
* `urbangreen_dw.dim_sensor_type`
* `urbangreen_dw.dim_user_farm_role`

They preserve history and use:

```text
ReplacingMergeTree(_version)
```

with:

* `valid_from`
* `valid_to`
* `is_current`

For current-state analysis, use `FINAL` before filtering:

```sql
SELECT farm_id, name, city, status
FROM urbangreen_dw.dim_farm FINAL
WHERE is_current = 1;
```

For historical analysis:

1. Deduplicate the dimension first.
2. Join the event timestamp to the half-open validity interval:

```text
[valid_from, valid_to)
```

Example:

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

---

## Facts and idempotent reloads

Fact tables may also use:

```text
ReplacingMergeTree(_loaded_at)
```

because loaders can replay the same business grain idempotently. Multiple physical versions may coexist before ClickHouse background merges complete.

Known examples include `urbangreen_dw.fact_harvests` and `urbangreen_dw.fact_farm_leaderboard` — confirm the engine for any other table via `describe_table` rather than assuming it is a plain `MergeTree`.

Before an aggregation that must not double-count replayed rows, use `FINAL` or equivalent `argMax` deduplication.

Example:

```sql
SELECT
    harvest_date,
    sum(weight_kg) AS total_yield_kg
FROM urbangreen_dw.fact_harvests FINAL
GROUP BY harvest_date
ORDER BY harvest_date;
```

Never aggregate — or directly select from — a `ReplacingMergeTree` fact table without considering whether physical duplicates may exist.

---

# Canonical metric rules

Unless explicitly stated otherwise:

* ratios return `NULL` when their denominator is zero or missing
* ratio values are fractions from `0.0` to `1.0`
* multiply by `100` only when a percentage is explicitly requested

The farm leaderboard is the one documented exception to the zero-denominator rule — see "Leaderboard zero fallback" below.

Do not replace a documented formula with a mathematically different aggregation.

---

## Total Harvest Yield

Source: `urbangreen_dw.fact_daily_farm_metrics`

Formula:

```sql
SUM(total_yield_kg)
```

Unit: kilograms.

---

## Yield Efficiency

Sources:

* `urbangreen_dw.fact_daily_farm_metrics`
* current version of `urbangreen_dw.dim_farm`

Unit: kilograms per square metre.

Calculate per farm over the selected date range:

```sql
SUM(total_yield_kg) / nullIf(MAX(size_m2), 0)
```

Do not use:

```sql
AVG(total_yield_kg / size_m2)
```

---

## Yield-per-Bed

Sources:

* `urbangreen_dw.fact_daily_farm_metrics`
* current version of `urbangreen_dw.dim_farm`

Unit: kilograms per bed.

Formula:

```sql
SUM(total_yield_kg) / nullIf(MAX(growing_beds_count), 0)
```

---

## Energy Efficiency

Source: `urbangreen_dw.fact_daily_farm_metrics`

Unit: kilowatt-hours per kilogram. Lower values indicate better energy efficiency.

Formula:

```sql
SUM(energy_kwh) / nullIf(SUM(total_yield_kg), 0)
```

Do not use:

```sql
AVG(energy_kwh / total_yield_kg)
```

When querying `urbangreen_dw.fact_farm_leaderboard`, use the precomputed `energy_efficiency_kwh_per_kg` value instead of rebuilding the metric.

---

## Total Energy Consumption

Source: `urbangreen_dw.fact_daily_farm_metrics`

Unit: kilowatt-hours.

Formula:

```sql
SUM(energy_kwh)
```

---

## Farm Expansion Progress

Source: current farms represented in the dashboard dataset.

Registered farm count:

```sql
COUNT(DISTINCT farm_id)
```

The dashboard target is `100` farms. Progress against the target:

```sql
COUNT(DISTINCT farm_id) / 100.0
```

Multiply by `100` only when a percentage is requested.

---

## Waste Reduction Progress

Source: `urbangreen_dw.fact_daily_farm_metrics`

Formula:

```sql
SUM(non_premium_yield_kg) / nullIf(SUM(total_yield_kg), 0)
```

Lower values indicate less non-premium output. This is the existing dashboard definition — it is not a comparison against a historical waste baseline.

---

## Environmental Compliance Rate

Also called: Sensor Compliance Rate.

Sources:

* `urbangreen_dw.fact_daily_farm_metrics`
* `urbangreen_dw.fact_daily_sensor_metrics`

Formula:

```sql
SUM(in_range_count) / nullIf(SUM(reading_count), 0)
```

Higher values indicate better compliance.

---

## Sensor Anomaly Rate

Source: `urbangreen_dw.fact_daily_sensor_metrics`

Formula:

```sql
SUM(anomaly_count) / nullIf(SUM(reading_count), 0)
```

Lower values indicate fewer anomalous readings.

---

## Average Sensor Value

Source: `urbangreen_dw.fact_daily_sensor_metrics`

Formula:

```sql
SUM(sum_value) / nullIf(SUM(reading_count), 0)
```

This is a weighted average. Never use:

```sql
AVG(sum_value / reading_count)
```

---

## Data Freshness

Source: `urbangreen_dw.fact_sensor_readings`

Unit: minutes since the most recent reading. Lower values mean fresher data.

Calculate per farm and sensor type:

```sql
dateDiff(
    'minute',
    max(reading_ts),
    now()
)
```

A missing value means that no sensor reading exists for the selected farm and sensor type.

---

# Leaderboard rules

Source: `urbangreen_dw.fact_farm_leaderboard`

Grain: one precomputed row per farm per day.

The following values are precomputed and must be read directly:

* `total_yield_kg`
* `premium_yield_share`
* `energy_efficiency_kwh_per_kg`
* `yield_rank`
* `quality_rank`
* `energy_rank`
* `composite_score`
* `composite_rank`

Do not independently rebuild these metrics or ranks when the leaderboard table is the appropriate source. For example, do not query the leaderboard and then calculate `RANK() OVER (ORDER BY energy_efficiency_kwh_per_kg)` to produce a new energy rank — read `energy_rank` directly.

## Leaderboard table is itself a ReplacingMergeTree fact table

`urbangreen_dw.fact_farm_leaderboard` is built as a `ReplacingMergeTree` table (sort key `(date_key, farm_id)`), so it carries the same pre-merge duplication risk as any other `ReplacingMergeTree` fact table described above. Apply `FINAL` (or equivalent `argMax` dedup) even when only reading precomputed columns like `energy_rank` or `composite_score` directly — not just when aggregating. Confirm the exact version column via `describe_table` before writing the query, since it is not repeated here.

## Leaderboard ranking behavior

The ETL computes each ranking axis independently per `metric_date` using `rank()` semantics:

* **Yield rank:** `total_yield_kg` descending.
* **Quality rank:** `premium_yield_share` descending.
* **Energy rank:** farms with yield ranked first, then `energy_efficiency_kwh_per_kg` ascending.
* **Composite rank:** `composite_score` descending.

Tied farms receive the same rank and the next rank contains a gap, matching `rank()` semantics. `composite_rank = 1` is the highest-ranked farm.

Always prefer these precomputed values over re-deriving them.

---

# Known data quirks and suspicious-result checks

A query returning successfully does not automatically mean the result is meaningful. Always sanity-check before presenting a potentially suspicious result. Look for:

* zero values inconsistent with the business context
* unexpected `NULL` values
* month-long ties
* many farms sharing exactly the same suspicious metric
* values inconsistent with the farm's infrastructure
* rankings dominated by likely missing-data artifacts
* ratios that appear unusually perfect, such as `0.0` or `1.0` for every entity

## Zero energy with real yield

A known UrbanGreen data anomaly is zero recorded energy despite real harvest yield. For example, farms may return `0.000 kWh/kg` energy efficiency while having non-zero harvest yield. On metered infrastructure, this can indicate missing or incomplete energy sensor data rather than genuinely perfect energy efficiency. Do not automatically interpret such farms as the most efficient.

If these values dominate the top energy-efficiency rankings, appear repeatedly over a long period, affect multiple farms, or conflict with expected metered infrastructure, flag them as suspicious and explain that the result may reflect missing energy readings rather than true performance.

A useful sanity check is to compare `total_yield_kg` with `energy_kwh` (or the corresponding energy data source) over the same period. If yield is positive while energy remains zero, explicitly mention the data-quality concern.

## Leaderboard zero fallback

The leaderboard ETL stores `0` for `premium_yield_share` and `energy_efficiency_kwh_per_kg` when `total_yield_kg = 0`. These zeros are storage fallbacks, not measured efficiency. Zero-yield farms are explicitly placed after farms with yield when `energy_rank` is computed. Do not interpret the stored zero efficiency as genuine performance — use the precomputed rank and understand its ETL behavior before explaining the result.

---

# Query execution rules

The MCP tool `execute_query` is read-only. It accepts one query that produces the requested result. Treat the following as constraints:

* use a single SQL statement
* query warehouse data only
* do not attempt writes
* do not use `INSERT`, `UPDATE`, `DELETE`, `ALTER`, or `DROP`
* do not use multi-statement SQL

Prefer one complete query that answers the user's question.

## Handling write requests

If the user asks to insert, update, or delete data, change a table, or create/drop database objects, do not attempt the request through `execute_query`. Clearly explain that `execute_query` is read-only and supports only a single read query. You may help formulate the requested write operation conceptually, but do not claim it was executed through the MCP server.

---

# Example workflows

## "Which farm had the best energy efficiency last month?"

1. Read `metrics` for the canonical Energy Efficiency definition.
2. Discover and describe `fact_farm_leaderboard` (and confirm it's the right source for a ranked, per-day question).
3. Read `conventions` — the leaderboard is a `ReplacingMergeTree` table, so `FINAL` applies here too.
4. Use the precomputed `energy_efficiency_kwh_per_kg` and `energy_rank` for the requested month.
5. Sanity-check whether the winning farm has positive yield and whether zero or near-zero energy efficiency is repeated across multiple farms, which would point to missing sensor data rather than genuine efficiency.
6. If suspicious, clearly flag the result rather than presenting it as genuine efficiency.

## "Compare the yield of Farm A and Farm B"

1. Read `metrics` for Total Harvest Yield.
2. Describe `fact_daily_farm_metrics` and confirm its engine via `describe_table`.
3. Read `conventions` and apply `FINAL`/`argMax` deduplication as needed.
4. Use `SUM(total_yield_kg)` rather than an alternative yield formula.
5. Execute one read-only query and compare the results.
6. Sanity-check for unexpected zeros or missing periods.

## "Is Farm X compliant?"

1. Read `metrics` for Environmental Compliance Rate.
2. Describe the relevant sensor or daily metrics table and read `conventions` if dedup applies.
3. Use `SUM(in_range_count) / nullIf(SUM(reading_count), 0)` — never `AVG(in_range_count / reading_count)`.
4. Execute one read-only query.
5. Check whether the denominator contains real readings. If no readings exist, do not report the farm as compliant merely because the ratio is absent or represented by a fallback value.

---

# Answering principles

When presenting the result:

1. State the result clearly.
2. Include the relevant date range or scope.
3. Use the canonical KPI meaning.
4. Distinguish measured performance from suspicious or missing-data artifacts.
5. Mention important limitations when they materially affect interpretation.
6. Do not claim that a zero, `NULL`, rank, or ratio has a business meaning without checking its documented warehouse semantics.

The goal is not only to produce syntactically valid SQL. The goal is to produce an answer that is schema-correct, metric-correct, deduplication-correct, semantically correct, and sanity-checked.