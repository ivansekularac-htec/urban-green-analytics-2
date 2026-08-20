from typing import Literal

from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app import prompts as prompt_handlers
from app import resources as resource_handlers
from app import tools as tool_handlers
from app.clickhouse import get_client
from app.config import get_settings

INSTRUCTIONS = """
UrbanGreen MCP provides read-only access to the UrbanGreen ClickHouse
warehouse, including its schema, metric definitions, and analytical data.

Do not call a tool until the user asks a warehouse question. Before the first
warehouse query in a session, call read_resource for
urbangreen://conventions. For KPIs and business metrics, also call
read_resource for urbangreen://metrics and use its canonical definition.

For warehouse questions, call list_tables for urbangreen_dw, then
describe_table for every table you plan to use, and only then call
execute_query. Queries must be read-only and must have an explicit LIMIT when
they return rows. Use only tables, columns, definitions, and values returned by
the server. Never invent database objects, formulas, measurements, rankings,
totals, or other numbers. Report tool errors and incomplete results clearly.
""".strip()


def create_mcp() -> FastMCP:
    """Build the UrbanGreen MCP server."""

    settings = get_settings()
    client = get_client()

    mcp = FastMCP(
        name="UrbanGreen MCP",
        instructions=INSTRUCTIONS,
    )

    @mcp.tool(name="list_tables")
    def list_tables(database: str = settings.clickhouse_db) -> dict:
        """List tables in an allowed ClickHouse database."""

        return tool_handlers.list_tables(
            client=client,
            database=database,
        )

    @mcp.tool(name="describe_table")
    def describe_table(
        table: str,
        database: str = settings.clickhouse_db,
    ) -> dict:
        """Describe the columns of a ClickHouse table."""

        return tool_handlers.describe_table(
            client=client,
            table=table,
            database=database,
        )

    @mcp.tool(name="execute_query")
    def execute_query(
        sql: str,
        limit: int | None = None,
    ) -> dict:
        """Execute a safe, read-only ClickHouse query."""

        return tool_handlers.execute_query(
            client=client,
            sql=sql,
            default_limit=settings.default_row_limit,
            max_limit=settings.max_row_limit,
            limit=limit,
        )

    @mcp.tool(name="read_resource")
    def read_resource(
        uri: Literal[
            "urbangreen://schema",
            "urbangreen://metrics",
            "urbangreen://conventions",
        ],
    ) -> dict[str, str]:
        """Read an UrbanGreen schema, metrics, or conventions resource.

        Use the exact URI shown in the ``uri`` argument. Read conventions
        before warehouse analysis and metrics before calculating a KPI.
        """

        return resource_handlers.read_warehouse_resource(
            client=client,
            database=settings.clickhouse_db,
            uri=uri,
        )

    @mcp.resource(
        resource_handlers.SCHEMA_URI,
        name="warehouse_schema",
        description="Current UrbanGreen ClickHouse warehouse schema.",
        mime_type="text/markdown",
    )
    def schema_resource() -> str:
        return resource_handlers.load_schema_markdown(
            client=client,
            database=settings.clickhouse_db,
        )

    mcp.resource(
        resource_handlers.METRICS_URI,
        name="metrics",
        description="Canonical UrbanGreen metric definitions.",
        mime_type="text/markdown",
    )(resource_handlers.metrics_resource)

    mcp.resource(
        resource_handlers.CONVENTIONS_URI,
        name="conventions",
        description="ClickHouse querying and warehouse conventions.",
        mime_type="text/markdown",
    )(resource_handlers.conventions_resource)

    mcp.prompt(prompt_handlers.analyze_metric)
    mcp.prompt(prompt_handlers.compare_farms)
    mcp.prompt(prompt_handlers.investigate_anomaly)

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        return JSONResponse({"status": "healthy"})

    return mcp
