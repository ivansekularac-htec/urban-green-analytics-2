"""The FastMCP server: one factory that registers everything the client sees.

The tools, resources and prompts are written as plain functions in their own
modules so they can be tested without a server. This module is where they
become MCP components, and it is the only place that knows about FastMCP.

It is a factory rather than a module-level server because building one opens
the ClickHouse connection. A module-level instance would make importing this
module - which the tests do - require a running warehouse.

The query functions take a ClickHouse client as their first argument. The model
must not see it, and FastMCP builds each schema from the signature it is given,
so those tools are registered through wrappers that close over the client. The
resource reader instead receives FastMCP's request context, which is also hidden
from its schema, and delegates to the resources already registered here.
"""

from functools import lru_cache

from clickhouse_connect.driver.client import Client
from fastmcp import FastMCP
from fastmcp.server.context import Context
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app import tools
from app.clickhouse import get_client
from app.config import get_settings
from app.metrics import track_tool
from app.prompts import analyze_metric, compare_farms, investigate_anomaly
from app.resources import (
    CONVENTIONS_URI,
    METRICS_URI,
    RESOURCE_URIS,
    SCHEMA_URI,
    WarehouseResourceName,
    conventions_resource,
    load_schema_markdown,
    metrics_resource,
)

# Sent to the MCP client during initialization. Whether and how the client
# includes these instructions in model context is controlled by the client.
INSTRUCTIONS = """Read-only access to the UrbanGreen ClickHouse warehouse, which holds daily
harvest and sensor metrics for the platform's farms.

Use read_warehouse_resource only when its guidance is relevant:
- conventions: before the first SQL query unless already present in the conversation
- metrics: for a KPI, metric, rate, efficiency, compliance, ranking, or formula
- schema: only for a broad warehouse overview; normally inspect relevant tables
  with list_tables and describe_table instead

Do not reread a resource already present in the conversation. Confirm every
table used in SQL with describe_table, then send one SELECT to execute_query.
The query tools return payloads: check `error` and `truncated` before reporting
what came back.

The analyze_metric, compare_farms and investigate_anomaly prompts carry the
same workflow for the questions users ask most.
"""

# Static resources need no factory-owned dependency. The live schema resource
# is registered separately inside create_server so it can close over the same
# ClickHouse client as the tools.
_STATIC_RESOURCES = (
    (METRICS_URI, "metrics", metrics_resource),
    (CONVENTIONS_URI, "conventions", conventions_resource),
)

_PROMPTS = (analyze_metric, compare_farms, investigate_anomaly)


def create_server(client: Client | None = None) -> FastMCP:
    """Build the server with every tool, resource, prompt and route registered.

    Args:
        client: ClickHouse client the tools and live schema resource should
            use. Defaults to the shared read-only client, and is supplied by
            tests that build a server without a warehouse behind it.
    """

    settings = get_settings()
    client = client if client is not None else get_client()

    mcp = FastMCP("UrbanGreen MCP", instructions=INSTRUCTIONS)

    # Keep track_tool below @mcp.tool so FastMCP receives the instrumented
    # callable while functools.wraps preserves the original tool signature.
    @mcp.tool
    @track_tool("list_tables")
    def list_tables(database: str = "urbangreen_dw") -> dict:
        """List the tables in a warehouse database.

        Returns the table names, or an `error` when the database is not one
        this server is allowed to read.
        """

        return tools.list_tables(client, database)

    @mcp.tool
    @track_tool("describe_table")
    def describe_table(table: str, database: str = "urbangreen_dw") -> dict:
        """Describe one table: column names, types, defaults and comments.

        Returns an `error` naming the table when it does not exist, so a bad
        guess can be corrected without running a query.
        """

        return tools.describe_table(client, table, database)

    @mcp.tool
    @track_tool("execute_query")
    def execute_query(sql: str, limit: int | None = None) -> dict:
        """Run one read-only SELECT against the warehouse.

        A row limit is applied whether or not the query carries one. The
        result reports the limit it used and sets `truncated` when rows were
        cut off; rejected SQL and ClickHouse failures come back as `error`.

        Args:
            sql: A single SELECT statement.
            limit: Optional lower ceiling on the rows returned.
        """

        return tools.execute_query(
            client,
            sql,
            default_limit=settings.default_row_limit,
            max_limit=settings.max_row_limit,
            limit=limit,
        )

    @mcp.tool
    @track_tool("read_warehouse_resource")
    async def read_warehouse_resource(
        resource: WarehouseResourceName,
        ctx: Context,
    ) -> str:
        """Read one registered UrbanGreen warehouse reference.

        Choose `conventions` for ClickHouse query rules, `metrics` for canonical
        KPI definitions, or `schema` only for a broad warehouse overview. For a
        normal query, prefer `describe_table` over loading the complete schema.

        Args:
            resource: Which warehouse reference to read.
        """

        result = await ctx.read_resource(RESOURCE_URIS[resource])

        if any(not isinstance(item.content, str) for item in result.contents):
            raise TypeError("UrbanGreen warehouse resources must contain text")

        return "\n\n".join(item.content for item in result.contents)

    @lru_cache(maxsize=1)
    def schema_resource() -> str:
        """Return the live warehouse DDL, cached for this server process."""

        return load_schema_markdown(client, settings.clickhouse_db)

    mcp.resource(SCHEMA_URI, name="schema", mime_type="text/markdown")(schema_resource)

    for uri, name, resource in _STATIC_RESOURCES:
        mcp.resource(uri, name=name, mime_type="text/markdown")(resource)

    for prompt in _PROMPTS:
        mcp.prompt(prompt)

    # Liveness only, and deliberately not a ClickHouse ping: compose already
    # holds this service back until the warehouse is healthy, and a restart
    # would not fix a warehouse that went away afterwards.
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    # Prometheus exposition is an HTTP concern rather than an MCP primitive,
    # so expose it as a Starlette route alongside the existing health route.
    @mcp.custom_route("/metrics", methods=["GET"])
    async def metrics(_request: Request) -> Response:
        """Expose the current Prometheus metrics."""
        return Response(
            content=generate_latest(),
            media_type=CONTENT_TYPE_LATEST,
        )

    return mcp
