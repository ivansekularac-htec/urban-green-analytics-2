"""
FastMCP server wiring for the UrbanGreen analytics service.

Builds one MCP server and registers its tools, resources, prompts,
compatibility tools, and HTTP health endpoint.
"""

from __future__ import annotations

import inspect
import logging
from collections.abc import Callable
from functools import lru_cache

from clickhouse_connect.driver.client import Client
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.clickhouse import get_client
from app.config import get_settings
from app.prompts import (
    analyze_metric,
    compare_farms,
    investigate_anomaly,
)
from app.resources import (
    CONVENTIONS_URI,
    METRICS_URI,
    SCHEMA_URI,
    conventions_resource,
    load_schema_markdown,
    metrics_resource,
)
from app.tools import (
    describe_table as describe_table_impl,
)
from app.tools import (
    execute_query as execute_query_impl,
)
from app.tools import (
    list_tables as list_tables_impl,
)

logger = logging.getLogger(__name__)

MCP_INSTRUCTIONS = """
UrbanGreen provides read-only analytical access to the ClickHouse warehouse.

Use read_resource for canonical metric definitions, warehouse schema, and
ClickHouse query conventions.

For supported analytical workflows, use get_prompt and follow the returned
procedure exactly.

Inspect relevant tables with describe_table before querying them, and use
execute_query only for safe read-only analysis.
""".strip()


def _format_prompt_signature(
    name: str,
    handler: Callable[..., str],
) -> str:
    """Render a compact model-facing prompt signature."""
    parameters = []

    for parameter in inspect.signature(handler).parameters.values():
        if parameter.default is inspect.Parameter.empty:
            parameters.append(parameter.name)
        else:
            parameters.append(f"{parameter.name}={parameter.default!r}")

    return f"{name}({', '.join(parameters)})"


def create_mcp_server(
    client: Client | None = None,
) -> FastMCP:
    """Build and configure the UrbanGreen MCP server."""
    settings = get_settings()

    if client is None:
        logger.info("Creating ClickHouse client")
        client = get_client()

    logger.info("Building UrbanGreen MCP server")

    mcp = FastMCP(
        "UrbanGreen MCP",
        instructions=MCP_INSTRUCTIONS,
    )

    # ------------------------------------------------------------------
    # Core tools
    # ------------------------------------------------------------------

    @mcp.tool(name="list_tables")
    def list_tables(
        database: str | None = None,
    ) -> dict[str, object]:
        """List tables in the default warehouse database unless another allowed database is requested."""
        return list_tables_impl(
            client,
            database=(database if database is not None else settings.clickhouse_db),
        )

    @mcp.tool(name="describe_table")
    def describe_table(
        table: str,
        database: str | None = None,
    ) -> dict[str, object]:
        """Describe a table in the default warehouse database unless another allowed database is requested."""
        return describe_table_impl(
            client,
            table=table,
            database=(database if database is not None else settings.clickhouse_db),
        )

    @mcp.tool(name="execute_query")
    def execute_query(
        sql: str,
        limit: int | None = None,
    ) -> dict[str, object]:
        """Execute a safe read-only ClickHouse query."""
        return execute_query_impl(
            client,
            sql,
            limit=limit,
            default_limit=settings.default_row_limit,
            max_limit=settings.max_row_limit,
        )

    # ------------------------------------------------------------------
    # Resource and prompt registries
    # ------------------------------------------------------------------

    resource_handlers: dict[str, Callable[[], str]] = {}
    prompt_handlers: dict[str, Callable[..., str]] = {}

    def register_resource(
        uri: str,
        handler: Callable[[], str],
    ) -> None:
        """Register one resource for native MCP and read_resource."""
        mcp.resource(uri)(handler)
        resource_handlers[uri] = handler

    def register_prompt(
        handler: Callable[..., str],
    ) -> None:
        """Register one prompt for native MCP and get_prompt."""
        mcp.prompt(handler)
        prompt_handlers[handler.__name__] = handler

    # ------------------------------------------------------------------
    # Resources
    # ------------------------------------------------------------------

    @lru_cache(maxsize=1)
    def schema_resource() -> str:
        """Return the live warehouse schema."""
        logger.info(f"Loading ClickHouse schema for database {settings.clickhouse_db}")

        return load_schema_markdown(
            client=client,
            database=settings.clickhouse_db,
        )

    register_resource(SCHEMA_URI, schema_resource)
    register_resource(METRICS_URI, metrics_resource)
    register_resource(CONVENTIONS_URI, conventions_resource)

    # ------------------------------------------------------------------
    # Prompts
    # ------------------------------------------------------------------

    register_prompt(analyze_metric)
    register_prompt(compare_farms)
    register_prompt(investigate_anomaly)

    # ------------------------------------------------------------------
    # Compatibility tool descriptions
    # ------------------------------------------------------------------
    # Build descriptions from the registries so discovery stays synchronized
    # automatically when resources or prompts are added.

    available_resources = "\n".join(f"- {uri}" for uri in resource_handlers)

    available_prompts = "\n".join(
        f"- {_format_prompt_signature(name, handler)}" for name, handler in prompt_handlers.items()
    )

    read_resource_description = f"""
Read one canonical UrbanGreen MCP resource by URI.

Available resources:
{available_resources}
""".strip()

    get_prompt_description = f"""
Render one canonical UrbanGreen analytical workflow.

Available prompts:
{available_prompts}

Pass the prompt parameters through the arguments object.
""".strip()

    # ------------------------------------------------------------------
    # Compatibility tools
    # ------------------------------------------------------------------

    @mcp.tool(
        name="read_resource",
        description=read_resource_description,
    )
    def read_resource_tool(
        uri: str,
    ) -> dict[str, object]:
        handler = resource_handlers.get(uri)

        if handler is None:
            return {
                "error": f"Unknown resource URI: {uri}",
                "available_resources": list(resource_handlers),
            }

        return {
            "uri": uri,
            "content": handler(),
        }

    @mcp.tool(
        name="get_prompt",
        description=get_prompt_description,
    )
    def get_prompt_tool(
        name: str,
        arguments: dict[str, object] | None = None,
    ) -> dict[str, object]:
        handler = prompt_handlers.get(name)

        if handler is None:
            return {
                "error": f"Unknown prompt: {name}",
                "available_prompts": list(prompt_handlers),
            }

        prompt_arguments = arguments or {}

        try:
            content = handler(**prompt_arguments)
        except TypeError as exc:
            return {
                "error": f"Invalid arguments for prompt '{name}': {exc}",
            }

        return {
            "name": name,
            "arguments": prompt_arguments,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
        }

    # ------------------------------------------------------------------
    # Plain HTTP routes
    # ------------------------------------------------------------------

    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(_request: Request) -> JSONResponse:
        """Return the MCP service health status."""
        return JSONResponse({"status": "healthy"})

    logger.info("UrbanGreen MCP server built successfully")

    return mcp
