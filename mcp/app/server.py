"""The FastMCP server: one factory that registers everything the client sees.

The tools, resources and prompts are written as plain functions in their own
modules so they can be tested without a server. This module is where they
become MCP components, and it is the only place that knows about FastMCP.

It is a factory rather than a module-level server because building one opens
the ClickHouse connection. A module-level instance would make importing this
module - which the tests do - require a running warehouse.

The tool functions take a ClickHouse client as their first argument. The model
must not see it, and FastMCP builds each schema from the signature it is given,
so the tools are registered through wrappers that close over the client. The
wrapper docstrings are the descriptions the model reads; the ones in tools.py
describe the same functions to a developer, down to the client argument itself.
"""

from clickhouse_connect.driver.client import Client
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import tools
from app.clickhouse import get_client
from app.config import get_settings
from app.prompts import analyze_metric, compare_farms, investigate_anomaly
from app.resources import (
    CONVENTIONS_URI,
    METRICS_URI,
    SCHEMA_URI,
    conventions_resource,
    metrics_resource,
    schema_resource,
)

# The first thing the client tells the model about this server. It names the
# resources by URI, because a model that has been told they exist still has to
# be told what to ask for.
INSTRUCTIONS = """Read-only access to the UrbanGreen ClickHouse warehouse, which holds daily
harvest and sensor metrics for the platform's farms.

Before writing SQL, read urbangreen://schema for the table definitions,
urbangreen://metrics for the canonical metric formulas, and
urbangreen://conventions for the ClickHouse rules the DDL does not show.

Confirm a table with describe_table before querying it, and send a single
SELECT to execute_query. Every tool returns a payload rather than raising:
check its `error` and `truncated` fields before reporting what came back.

The analyze_metric, compare_farms and investigate_anomaly prompts already
carry these steps for the questions users ask most.
"""

# Named for the client, not for the function that builds them.
_RESOURCES = (
    (SCHEMA_URI, "schema", schema_resource),
    (METRICS_URI, "metrics", metrics_resource),
    (CONVENTIONS_URI, "conventions", conventions_resource),
)

_PROMPTS = (analyze_metric, compare_farms, investigate_anomaly)


def create_server(client: Client | None = None) -> FastMCP:
    """Build the server with every tool, resource, prompt and route registered.

    Args:
        client: ClickHouse client the tools should use. Defaults to the shared
            read-only client, and is supplied by tests that build a server
            without a warehouse behind it.
    """

    settings = get_settings()
    client = client or get_client()

    mcp = FastMCP("UrbanGreen MCP", instructions=INSTRUCTIONS)

    @mcp.tool
    def list_tables(database: str = "urbangreen_dw") -> dict:
        """List the tables in a warehouse database.

        Returns the table names, or an `error` when the database is not one
        this server is allowed to read.
        """

        return tools.list_tables(client, database)

    @mcp.tool
    def describe_table(table: str, database: str = "urbangreen_dw") -> dict:
        """Describe one table: column names, types, defaults and comments.

        Returns an `error` naming the table when it does not exist, so a bad
        guess can be corrected without running a query.
        """

        return tools.describe_table(client, table, database)

    @mcp.tool
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

    for uri, name, resource in _RESOURCES:
        mcp.resource(uri, name=name, mime_type="text/markdown")(resource)

    for prompt in _PROMPTS:
        mcp.prompt(prompt)

    # Liveness only, and deliberately not a ClickHouse ping: compose already
    # holds this service back until the warehouse is healthy, and a restart
    # would not fix a warehouse that went away afterwards.
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    return mcp
