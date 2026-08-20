# UrbanGreen MCP

UrbanGreen MCP gives Claude Desktop and other MCP clients read-only access to
the UrbanGreen ClickHouse warehouse. It provides safe SQL execution, schema
discovery, canonical metric definitions, warehouse conventions, and reusable
analysis workflows.

## Server capabilities

The server advertises four tools, three resources, and three prompts from one
FastMCP instance.

### Tools

- `list_tables` lists tables in the allowed `urbangreen_dw` or `etl` database.
- `describe_table` returns column metadata for one allowed table.
- `execute_query` validates and runs a read-only ClickHouse query with enforced
  row limits.
- `read_resource` gives the model controlled access to one of the three
  registered UrbanGreen resources.

`read_resource` accepts only these exact URI values:

- `urbangreen://schema`
- `urbangreen://metrics`
- `urbangreen://conventions`

It returns the resource URI, `text/markdown` MIME type, and Markdown content.
It cannot read arbitrary files, websites, or unregistered URIs.

### Resources

- `urbangreen://schema` contains the current schema introspected from
  ClickHouse.
- `urbangreen://metrics` contains canonical KPI definitions, formulas, units,
  source tables, and ranking direction.
- `urbangreen://conventions` contains ClickHouse and UrbanGreen warehouse query
  rules.

The resources remain native MCP resources. `read_resource` is an additional
model-controlled access path and uses the same underlying content; it does not
keep a second copy of the documents.

### Prompts

- `analyze_metric` analyses one canonical metric over a requested data window.
- `compare_farms` compares selected farms on a canonical metric.
- `investigate_anomaly` investigates anomalous readings for a farm and sensor
  type.

Prompts are user-selected workflows. They do not execute SQL by themselves;
they instruct Claude which resources and tools to use and in which order.

## Start the server

From the repository root, build and start the MCP service:

```bash
docker compose up -d --build urbangreen-mcp
```

The service waits for `urbangreen-clickhouse` to become healthy before it
starts. Check the service from the machine on which Claude Desktop runs:

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{"status":"healthy"}
```

Port `8001` is the default `MCP_PORT`. If `.env` uses a different value, use
that port in both the health check and the MCP connection. The Streamable HTTP
endpoint is:

```text
http://localhost:8001/mcp
```

## Claude Desktop

This project assumes the UrbanGreen MCP connection has already been added to
Claude Desktop. Connection setup can differ depending on whether the server is
reached through a local MCP bridge or a publicly reachable remote connector,
so connection credentials and machine-specific configuration do not belong in
this repository.

After rebuilding or restarting the MCP container:

1. Reconnect the UrbanGreen connector, or fully quit and reopen Claude Desktop,
   so it refreshes the server capabilities.
2. Open a new chat.
3. Use the **+** button beside the chat input and open **Connectors** to confirm
   that UrbanGreen is connected and enabled.
4. Confirm that the connector exposes the four tools listed above.

No client-side system prompt or Preset is required. The FastMCP server sends
its own instructions to Claude. Those instructions require this warehouse
flow:

1. Read `urbangreen://conventions` through `read_resource` before the first
   warehouse query in a session.
2. Call `list_tables`.
3. Call `describe_table` for every table that will be queried.
4. For KPIs and business metrics, read `urbangreen://metrics` through
   `read_resource` and use its canonical definition.
5. Call `execute_query` with read-only SQL and an explicit `LIMIT` whenever the
   query returns rows.
6. Use only server-provided database objects, definitions, and values; never
   invent numbers.

## Using native resources and prompts

Claude Desktop exposes native MCP resources as context attachments and MCP
prompts as user-selected commands or workflows. Their exact location can vary
between Claude Desktop releases.

When a native resource is attached by the user, Claude receives its content as
conversation context. When Claude needs to fetch a resource autonomously, it
should use `read_resource`.

To use a server prompt, select one of `analyze_metric`, `compare_farms`, or
`investigate_anomaly` from the UrbanGreen connector's available prompts and
provide its requested arguments. Each prompt tells Claude to read the required
resources before querying the warehouse.

## Smoke tests

### 1. Tool discovery

Ask without allowing a tool call:

```text
List the exact names of the UrbanGreen MCP tools available to you. Do not call
them yet.
```

Expected tools:

```text
list_tables
describe_table
execute_query
read_resource
```

If `read_resource` is missing, rebuild the container and reconnect the server
so Claude Desktop refreshes its tool list.

### 2. Resource access

```text
Call read_resource with uri="urbangreen://conventions". Summarize the first
three warehouse rules returned by the tool. Do not query ClickHouse.
```

Claude should call `read_resource` exactly once and base its answer on the
returned conventions document.

Then verify the metrics document:

```text
Call read_resource with uri="urbangreen://metrics" and explain the canonical
definition of Energy Efficiency. Do not query ClickHouse.
```

The answer must use the formula, unit, source tables, and direction returned by
the resource rather than reconstructing them from general knowledge.

### 3. Warehouse query workflow

```text
List the available UrbanGreen warehouse tables, describe the farm dimension,
and return at most five farms. Follow the server's required tool order.
```

Claude should call `read_resource` for conventions, then `list_tables`,
`describe_table`, and `execute_query`. The executed query must be read-only and
contain `LIMIT 5` or a stricter limit.

### 4. Native prompt

Select the `analyze_metric` MCP prompt in Claude Desktop and provide:

```text
metric: Energy Efficiency
days: 30
```

Claude should follow the rendered workflow, read both required resources,
describe the selected tables, and execute one final query.

## Troubleshooting

If the connector is not available, first verify the server independently:

```bash
curl http://localhost:8001/health
docker compose ps urbangreen-clickhouse urbangreen-mcp
docker compose logs --no-color --tail=100 urbangreen-mcp
```

If `/health` fails, check `MCP_PORT`, Docker port publishing, ClickHouse health,
and virtual-machine port forwarding. If `/health` succeeds but Claude Desktop
does not connect, inspect the connector configuration and Claude Desktop's MCP
logs, then fully restart the application.

If Claude sees only three tools, it has cached an older server capability list.
Rebuild `urbangreen-mcp` and reconnect it. If Claude cannot access a native MCP
resource in the UI, use `read_resource`; all three resources are available
through that tool.
