"""
Tests for UrbanGreen FastMCP server wiring.

Verifies the public MCP component contract, compatibility tools,
shared ClickHouse access, server instructions, and HTTP health endpoint.
"""

from unittest.mock import MagicMock

import pytest
from fastmcp import Client
from starlette.testclient import TestClient

import app.server as server_module
from app.prompts import analyze_metric
from app.resources import (
    CONVENTIONS_URI,
    METRICS_URI,
    SCHEMA_URI,
    metrics_resource,
)
from app.server import create_mcp_server


@pytest.fixture
def clickhouse_client() -> MagicMock:
    """Provide a fake shared ClickHouse client."""
    return MagicMock()


@pytest.fixture
def mcp_server(clickhouse_client: MagicMock):
    """Build an MCP server without opening a real ClickHouse connection."""
    return create_mcp_server(client=clickhouse_client)


@pytest.mark.anyio
async def test_server_exposes_expected_mcp_components(mcp_server):
    async with Client(mcp_server) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        prompts = await client.list_prompts()

    assert {tool.name for tool in tools} == {
        "list_tables",
        "describe_table",
        "execute_query",
        "read_resource",
        "get_prompt",
    }

    assert {str(resource.uri) for resource in resources} == {
        SCHEMA_URI,
        METRICS_URI,
        CONVENTIONS_URI,
    }

    assert {prompt.name for prompt in prompts} == {
        "analyze_metric",
        "compare_farms",
        "investigate_anomaly",
    }


@pytest.mark.anyio
async def test_read_resource_tool_returns_registered_resource(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "read_resource",
            {
                "uri": METRICS_URI,
            },
        )

    assert result.data == {
        "uri": METRICS_URI,
        "content": metrics_resource(),
    }


@pytest.mark.anyio
async def test_read_resource_tool_rejects_unknown_uri(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "read_resource",
            {
                "uri": "urbangreen://unknown",
            },
        )

    assert result.data["error"] == ("Unknown resource URI: urbangreen://unknown")
    assert set(result.data["available_resources"]) == {
        SCHEMA_URI,
        METRICS_URI,
        CONVENTIONS_URI,
    }


@pytest.mark.anyio
async def test_get_prompt_tool_renders_registered_prompt(mcp_server):
    arguments = {
        "metric": "Energy Efficiency",
        "days": 14,
    }

    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "get_prompt",
            {
                "name": "analyze_metric",
                "arguments": arguments,
            },
        )

    assert result.data["name"] == "analyze_metric"
    assert result.data["arguments"] == arguments
    assert result.data["messages"] == [
        {
            "role": "user",
            "content": analyze_metric(**arguments),
        }
    ]


@pytest.mark.anyio
async def test_get_prompt_tool_rejects_unknown_prompt(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "get_prompt",
            {
                "name": "unknown_prompt",
            },
        )

    assert result.data["error"] == "Unknown prompt: unknown_prompt"
    assert set(result.data["available_prompts"]) == {
        "analyze_metric",
        "compare_farms",
        "investigate_anomaly",
    }


@pytest.mark.anyio
async def test_get_prompt_tool_rejects_invalid_arguments(mcp_server):
    async with Client(mcp_server) as client:
        result = await client.call_tool(
            "get_prompt",
            {
                "name": "analyze_metric",
                "arguments": {
                    "unknown_argument": "value",
                },
            },
        )

    assert result.data["error"].startswith("Invalid arguments for prompt 'analyze_metric':")


def test_server_creates_clickhouse_client_once(monkeypatch):
    clickhouse_client = MagicMock()
    get_client = MagicMock(return_value=clickhouse_client)

    monkeypatch.setattr(
        server_module,
        "get_client",
        get_client,
    )

    create_mcp_server()

    get_client.assert_called_once_with()


@pytest.mark.anyio
async def test_schema_resource_uses_shared_clickhouse_client(
    mcp_server,
    clickhouse_client,
):
    clickhouse_client.query.return_value.result_rows = []

    async with Client(mcp_server) as client:
        await client.read_resource(SCHEMA_URI)

    clickhouse_client.query.assert_called_once()


def test_server_has_instructions(mcp_server):
    assert mcp_server.instructions


def test_health_endpoint_returns_200(mcp_server):
    app = mcp_server.http_app()

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
