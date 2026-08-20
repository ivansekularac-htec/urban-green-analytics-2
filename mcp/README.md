# UrbanGreen MCP

UrbanGreen MCP provides read-only analytical access to the UrbanGreen ClickHouse data warehouse through the Model Context Protocol (MCP).

The service exposes warehouse metadata, safe SQL execution, canonical business definitions, warehouse conventions, and reusable analytical workflows to MCP clients such as Claude Desktop.

## Architecture

The MCP interface is split into three responsibilities:

```text
Tools
    → access ClickHouse metadata and data

Resources
    → canonical warehouse knowledge

Prompts
    → reusable analytical workflows
```

The server also exposes two compatibility tools:

```text
read_resource
get_prompt
```

These allow tool-oriented MCP clients to access the same registered resources and prompts without duplicating their content or logic.

The resulting model-facing tool surface is intentionally kept small:

```text
list_tables
describe_table
execute_query
read_resource
get_prompt
```

---

## Running the Service

The MCP service runs as part of the project Docker Compose stack.

Build and start the containers:

```powershell
docker compose up urbangreen-mcp -d --build
```

Check their status:

```powershell
docker compose ps
```

The default local MCP endpoint is:

```text
http://localhost:8001/mcp
```

The service also exposes a health endpoint:

```text
http://localhost:8001/health
```

The stack can be stopped with:

```powershell
docker compose down
```

---

## MCP Tools

### `list_tables`

Lists tables from an allowed ClickHouse database.

Parameters:

```text
database: str | None
```

If `database` is omitted, the configured warehouse database is used.

Example:

```text
list_tables(database="urbangreen_dw")
```

---

### `describe_table`

Returns metadata for a warehouse table.

Parameters:

```text
table: str
database: str | None
```

The returned metadata includes:

* column name
* ClickHouse type
* default kind
* default expression
* column comment

Column comments provide additional semantic context that can be used when generating analytical SQL.

Example:

```text
describe_table(
    table="fact_daily_farm_metrics",
    database="urbangreen_dw"
)
```

---

### `execute_query`

Executes validated read-only ClickHouse SQL.

Parameters:

```text
sql: str
limit: int | None
```

Queries pass through the SQL safety layer before execution.

The result payload contains:

```text
sql
limit
columns
rows
row_count
truncated
```

Validation and ClickHouse errors are returned as structured payloads so the model can handle them without losing the analytical workflow.

---

### `read_resource`

Provides model-callable access to registered UrbanGreen MCP resources.

Parameter:

```text
uri: str
```

Available resources:

```text
urbangreen://schema
urbangreen://metrics
urbangreen://conventions
```

Example:

```text
read_resource(uri="urbangreen://metrics")
```

The tool delegates directly to the same handlers used by the native MCP resources.

---

### `get_prompt`

Returns a registered UrbanGreen analytical workflow.

Parameters:

```text
name: str
arguments: dict | None
```

Available workflows:

```text
analyze_metric(metric, days=30)
compare_farms(farm_ids, dimension="yield", days=30)
investigate_anomaly(farm_id, sensor_type, days=7)
```

Example:

```text
get_prompt(
    name="analyze_metric",
    arguments={
        "metric": "Energy Efficiency",
        "days": 30
    }
)
```

The returned prompt defines the procedure the model should follow for the requested analytical task.

---

## MCP Resources

### `urbangreen://schema`

Contains the current ClickHouse warehouse schema.

The resource is generated from the live warehouse and contains the registered table definitions.

It is used when the model needs to discover warehouse structure.

---

### `urbangreen://metrics`

Contains the canonical UrbanGreen metric catalog.

It defines business metrics including their:

* business name
* formula
* unit
* source tables
* ranking direction
* metric-specific rules

Canonical formulas are kept here rather than repeated inside prompts.

Examples include:

* Total Harvest Yield
* Yield Efficiency
* Yield-per-Bed
* Energy Efficiency
* Total Energy Consumption
* Environmental Compliance Rate
* Sensor Anomaly Rate
* Average Sensor Value
* Data Freshness
* Farm Leaderboard

---

### `urbangreen://conventions`

Contains ClickHouse and warehouse rules that cannot be reliably inferred from table DDL alone.

These include:

* Type-1 dimension handling
* Type-2 slowly changing dimensions
* `FINAL`
* `argMax`
* historical validity joins
* fact-table deduplication
* idempotent reload behavior

Analytical SQL should follow these conventions.

---

## MCP Prompts

Prompts define analytical procedure rather than business formulas.

The formulas and warehouse rules remain in MCP resources so that there is a single canonical source for each rule.

### `analyze_metric`

Analyzes one canonical warehouse metric over a recent data-backed period.

The workflow:

1. reads the metric definition from `urbangreen://metrics`
2. reads warehouse conventions from `urbangreen://conventions`
3. inspects the required table structure
4. anchors the requested period to the newest available warehouse data
5. executes the analytical query
6. reports the value, unit, date range, and source table

Example request:

```text
Analyze Energy Efficiency over the last 30 days using the UrbanGreen MCP.
Use the canonical UrbanGreen workflow if one exists.
```

---

### `compare_farms`

Compares farms using a canonical warehouse metric.

The workflow selects the correct aggregate or precomputed fact table, resolves farm names, applies warehouse conventions, and orders the result according to the metric direction.

Example:

```text
Compare farms 1, 2 and 3 on energy efficiency over the last 30 days.
Use the canonical UrbanGreen workflow.
```

---

### `investigate_anomaly`

Investigates anomalous sensor behavior for a farm and sensor type.

The workflow uses canonical anomaly definitions, daily sensor aggregates, current sensor metadata, and stored anomaly classifications.

Atomic sensor readings are only queried when they are explicitly needed.

Example:

```text
Investigate Temperature anomalies for farm 5 over the last 7 days.
Use the canonical UrbanGreen workflow.
```

---

## Claude Desktop

Claude Desktop can use the UrbanGreen MCP service through:

```text
http://localhost:8001/mcp
```

The MCP server provides its own usage instructions and exposes the following model-callable tools:

```text
list_tables
describe_table
execute_query
read_resource
get_prompt
```

No separate Claude system prompt is currently required.

For canonical analytical tasks, the user can ask Claude to use the UrbanGreen workflow when one exists.

Example:

```text
Analyze Total Energy Consumption over the last 30 days using the UrbanGreen MCP.

Use the canonical UrbanGreen workflow if one exists.
Do not invent metric definitions, columns, or dates.
```

For an `analyze_metric` request, the normal workflow is:

```text
get_prompt
    ↓
read_resource(urbangreen://metrics)
    ↓
read_resource(urbangreen://conventions)
    ↓
describe_table
    ↓
execute_query
    ↓
answer
```

For ad-hoc analytical questions, Claude can use the same resources and core query tools directly.

---

## Inspecting the MCP Interface

The currently registered MCP interface can be inspected with:

```powershell
uv run fastmcp list http://localhost:8001/mcp --resources --prompts
```

The current server exposes:

```text
Tools (5)
- list_tables
- describe_table
- execute_query
- read_resource
- get_prompt

Resources (3)
- urbangreen://schema
- urbangreen://metrics
- urbangreen://conventions

Prompts (3)
- analyze_metric
- compare_farms
- investigate_anomaly
```

A tool can also be invoked directly from the CLI:

```powershell
uv run fastmcp call http://localhost:8001/mcp list_tables database=urbangreen_dw --auth none --json
```

For example, a resource can be read through the compatibility tool with:

```powershell
uv run fastmcp call http://localhost:8001/mcp read_resource uri=urbangreen://conventions --auth none --json
```

---

## Design Decisions

### Canonical knowledge lives in resources

Metric definitions and warehouse conventions are not duplicated across analytical prompts.

```text
metrics resource
    → business formulas and units

conventions resource
    → ClickHouse and warehouse rules

schema resource
    → live warehouse structure
```

### Prompts define procedure

Prompts describe which resources and tools to use, in which order, and how to interpret the returned payload.

They do not duplicate canonical metric definitions.

### Resources and prompts remain native MCP components

The server continues to register native MCP Resources and Prompts.

`read_resource` and `get_prompt` only provide an additional model-callable path for clients where native resources or prompts cannot be invoked directly by the model.

### Compatibility tools are registry-driven

Registered resources and prompts are shared between the native MCP interface and compatibility tools.

Adding a new resource or prompt therefore requires only one registration and does not require maintaining a separate compatibility implementation.

### Warehouse access is read-only

All analytical SQL passes through the SQL safety layer before reaching ClickHouse.

Database access is limited to explicitly allowed databases, and query results are bounded by configured row limits.
