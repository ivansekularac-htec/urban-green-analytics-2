"""Tests for the configured FastMCP server factory."""

import asyncio
from types import SimpleNamespace
from unittest.mock import Mock, patch

import httpx

from app.server import INSTRUCTIONS, create_mcp


def test_factory_registers_core_tools_with_one_clickhouse_client():
    settings = SimpleNamespace(
        clickhouse_db="urbangreen_dw",
        default_row_limit=100,
        max_row_limit=1000,
    )
    client = Mock()

    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.server.get_client", return_value=client) as get_client,
    ):
        mcp = create_mcp()

    tools = asyncio.run(mcp.list_tools())
    resources = asyncio.run(mcp.list_resources())
    prompts = asyncio.run(mcp.list_prompts())

    assert {tool.name for tool in tools} == {
        "list_tables",
        "describe_table",
        "execute_query",
        "read_resource",
    }
    assert {str(resource.uri) for resource in resources} == {
        "urbangreen://schema",
        "urbangreen://metrics",
        "urbangreen://conventions",
    }
    assert {prompt.name for prompt in prompts} == {
        "analyze_metric",
        "compare_farms",
        "investigate_anomaly",
    }
    assert mcp.instructions == INSTRUCTIONS
    get_client.assert_called_once_with()


def test_read_resource_tool_uses_registered_resource_handler():
    settings = SimpleNamespace(
        clickhouse_db="urbangreen_dw",
        default_row_limit=100,
        max_row_limit=1000,
    )
    client = Mock()

    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.server.get_client", return_value=client),
    ):
        mcp = create_mcp()

    expected = {
        "uri": "urbangreen://conventions",
        "mime_type": "text/markdown",
        "content": "# Conventions\n",
    }

    with patch(
        "app.server.resource_handlers.read_warehouse_resource",
        return_value=expected,
    ) as read_resource:
        result = asyncio.run(
            mcp.call_tool(
                "read_resource",
                {"uri": "urbangreen://conventions"},
            ),
        )

    assert result.structured_content == expected
    read_resource.assert_called_once_with(
        client=client,
        database="urbangreen_dw",
        uri="urbangreen://conventions",
    )


def test_schema_resource_uses_factory_clickhouse_client():
    settings = SimpleNamespace(
        clickhouse_db="urbangreen_dw",
        default_row_limit=100,
        max_row_limit=1000,
    )
    client = Mock()

    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.server.get_client", return_value=client),
    ):
        mcp = create_mcp()

    with patch(
        "app.server.resource_handlers.load_schema_markdown",
        return_value="# Warehouse schema\n",
    ) as load_schema:
        asyncio.run(mcp.read_resource("urbangreen://schema"))

    load_schema.assert_called_once_with(
        client=client,
        database="urbangreen_dw",
    )


def test_health_route_returns_200_without_authentication():
    settings = SimpleNamespace(
        clickhouse_db="urbangreen_dw",
        default_row_limit=100,
        max_row_limit=1000,
    )

    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.server.get_client", return_value=Mock()),
    ):
        mcp = create_mcp()

    async def request_health() -> httpx.Response:
        transport = httpx.ASGITransport(
            app=mcp.http_app(transport="http"),
        )

        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            return await client.get("/health")

    response = asyncio.run(request_health())

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
