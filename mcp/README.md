# urbangreen-mcp

An MCP server that gives a local model read-only access to the Urban Green
ClickHouse warehouse. It exposes five tools, three resources and three prompts
over streamable HTTP, and answers `/health` for the compose healthcheck.

Nothing here writes. The ClickHouse session runs with `readonly=2`, every
statement is parsed and rewritten to carry a row limit before it runs, and the
result is capped server-side.

## Running it

The server comes up with the rest of the stack:

```
docker compose --profile analytics up -d urbangreen-mcp
docker compose ps urbangreen-mcp
curl -i http://localhost:8001/health
```

It listens on `${MCP_PORT}` (8001 by default) and publishes that port to
`127.0.0.1`, so a client on the same machine can reach it. The MCP endpoint is
at `/mcp`; `/health` is a plain HTTP route beside it and needs no handshake.

After editing `docker-compose.yaml`, recreate rather than restart -
`docker compose restart` reuses the container's existing environment:

```
docker compose up -d --force-recreate urbangreen-mcp
```

## What is registered

| Tools | Resources | Prompts |
| --- | --- | --- |
| `read_resource` | `urbangreen://schema` | `analyze_metric` |
| `get_prompt` | `urbangreen://metrics` | `compare_farms` |
| `list_tables` | `urbangreen://conventions` | `investigate_anomaly` |
| `describe_table` | | |
| `execute_query` | | |

The server writes what it registered to its log on every start, which is the
first place to look if a client shows the wrong counts:

```
docker logs urbangreen-mcp | head -1
INFO:app.server:registered 5 tool(s), 3 resource(s), 3 prompt(s) against urbangreen_dw
```

`chart_query` belongs to T5.2.7 and is not built yet, so a client missing it
does not mean the wiring is broken.

## Why `read_resource` and `get_prompt` exist

Under MCP the three primitives have different owners. A **tool** is invoked by
the model. A **resource** is read by the client, which decides whether to offer
it - usually as something the user attaches to a message. A **prompt** is picked
by the user, normally from a menu.

A client that implements tools and nothing else therefore leaves the other two
unreachable, and both clients used here behave that way: LM Studio lists tools
only, and Claude Desktop shows the connector as a toggle with no way to attach a
resource or pick a prompt. Without a tool the model never reads
`urbangreen://conventions`, and writes SQL without knowing which tables need
`FINAL` or that a fact joins a dimension on `farm_id` rather than `farm_key`.

The two tools close that gap. Each reads the same registry the registration loop
reads, so a fourth resource or prompt needs no change to either, and neither can
serve something the server does not. Both answer a bad argument with what would
have worked - an unknown URI comes back with the ones that are served, and a
misspelled prompt argument comes back with the parameters the template takes -
so a wrong guess costs one call rather than the answer.

Only these two, rather than FastMCP's `ResourcesAsTools` and `PromptsAsTools`
transforms. Those add a `list_*` beside every read, so the same coverage costs
seven tools instead of five for a small local model to choose between. The URIs
and prompt names are already in the server instructions, so the listing tools
would spend that attention on something the model has been told.

In a client that does surface resources and prompts, both still work the normal
way - the tools are an addition, not a replacement.

## LM Studio wiring

Settings → Integrations → MCP → Add MCP Server, then paste:

```json
{
  "mcpServers": {
    "urbangreen": {
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

Use the literal port. `mcp.json` does not expand `${MCP_PORT}`, so if you
changed it in `.env`, change it here too.

Save, and the entry should flip to **Connected** with five tools listed. It
shows no resources or prompts, which is the client limitation described above,
not a server fault. If it stays disconnected, check
`curl http://localhost:8001/health` first - that separates a server problem from
a client one.

## System prompt (paste into LM Studio)

Open a new chat, paste this into the system-message field, and save it as a
Preset so it carries across chats.

```text
You answer questions about the Urban Green vertical farms by querying the
ClickHouse warehouse through the tools you have been given. You never answer a
question about the data from memory.

At the start of a session, call read_resource with urbangreen://conventions
once. It carries the rules that change the numbers - which tables must be read
with FINAL, which column a fact joins to a dimension on, when a window has to be
anchored to the newest loaded date. Apply it to every query you write
afterwards.

When a question names a metric - yield efficiency, energy efficiency, premium
share, compliance rate, the farm leaderboard - call read_resource with
urbangreen://metrics and use the definition written there. Do not derive your
own formula, and do not recompute a value the warehouse already stores. Read
urbangreen://schema the same way when you need the DDL of a table.

When a question is an analysis of one metric, a comparison of farms, or an
investigation of a sensor anomaly, call get_prompt for analyze_metric,
compare_farms or investigate_anomaly first and follow the procedure it returns.

Work in this order: list_tables to find the table, describe_table to see its
columns and their comments, then execute_query. Describe every table you are
about to read before you write SQL against it, so you use columns that exist
rather than columns you expect.

Write an explicit LIMIT in every query. The server adds one if you leave it out,
but then the number you get back is not the number you asked for.

Read the payload execute_query returns, not just its rows:

- if it carries `error`, correct the query once and try again; if that also
  fails, report the error text rather than guessing at variations
- if it carries `truncated: true`, the row limit cut the result short - say so,
  and do not present a total or a ranking built from it as complete
- a NULL is an answer, not a zero: the canonical formulas divide with nullIf, so
  NULL means the denominator was zero and there was nothing to measure

Report only numbers that came back from a query. State the table each number
came from and the date range you filtered on. If the data does not answer the
question, say so. Never fill a gap with an estimate.
```

## Verifying the wiring

Ask in a fresh chat:

```
What tools and resources do you have access to?
```

The model should enumerate five tools. If it sees none of them, the client is
not connected. If the count is lower, check the registration line in the server
log.

Then a real one, which exercises the whole path:

```
Which farm had the highest yield last month, and which was lowest?
```

Expect it to call `read_resource` for the conventions, look the metric up,
describe the table, and come back with farm names rather than ids.

## Development

```
cd mcp
uv sync --frozen
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Configuration comes from the root `.env`. `MCP_*` names are this service's own
policy - row limits, query timeout, memory ceiling - while `CLICKHOUSE_*` are the
connection details shared with the rest of the stack.
