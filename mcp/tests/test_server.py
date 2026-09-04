"""
Tests for the server factory.

The components themselves are tested in their own modules; what is asserted
here is the wiring. A tool registered under the wrong name, a resource under
the wrong URI, or a ClickHouse client leaking into a schema are all failures
that the unit tests cannot see, because the functions are correct either way.

The factory is exercised through an in-memory client, so what these tests read
is what an MCP client would be told.
"""

import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
from fastmcp import Client

from app import server as server_module
from app.config import get_settings
from app.resources import CONVENTIONS_URI, METRICS_URI, RESOURCE_URIS, SCHEMA_URI
from app.server import create_server


def build_server(client: MagicMock | None = None):
    """Build a fully registered server with no warehouse behind it."""

    return create_server(client=client if client is not None else MagicMock())


def query(server, call):
    """Run one call against the server over an in-memory client session."""

    async def session():
        async with Client(server) as client:
            return await call(client)

    return asyncio.run(session())


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------


def test_the_server_registers_every_component_the_client_needs():
    server = build_server()

    tools = query(server, lambda client: client.list_tools())
    prompts = query(server, lambda client: client.list_prompts())

    assert [tool.name for tool in tools] == [
        "list_tables",
        "describe_table",
        "execute_query",
        "read_warehouse_resource",
    ]
    assert [prompt.name for prompt in prompts] == [
        "analyze_metric",
        "compare_farms",
        "investigate_anomaly",
    ]


def test_resources_are_published_under_the_shared_uris():
    """The prompts send the model to these URIs by importing the same
    constants, so a resource registered elsewhere is unreachable rather than
    broken, and nothing raises."""
    server = build_server()

    resources = query(server, lambda client: client.list_resources())

    assert {str(resource.uri) for resource in resources} == {
        SCHEMA_URI,
        METRICS_URI,
        CONVENTIONS_URI,
    }


def test_the_server_advertises_resource_guidance_during_initialization():
    """Instructions are MCP initialization metadata; the client decides whether
    to place them in model context."""
    server = build_server()

    async def initialize():
        async with Client(server) as client:
            return client.initialize_result.instructions

    instructions = asyncio.run(initialize())

    assert "read_warehouse_resource" in instructions
    assert all(resource in instructions for resource in RESOURCE_URIS)


# ---------------------------------------------------------------------------
# What the tool schemas expose
# ---------------------------------------------------------------------------


def test_no_tool_exposes_the_clickhouse_client():
    """The tools in app.tools take the client as their first argument. It is
    supplied by the factory, and a model that could pass one would be choosing
    the connection the query runs on."""
    server = build_server()

    tools = query(server, lambda client: client.list_tools())

    for tool in tools:
        assert "client" not in tool.inputSchema["properties"]
        assert "ctx" not in tool.inputSchema["properties"]


def test_resource_reader_exposes_only_the_three_stable_names():
    """An enum prevents the model from inventing names or passing arbitrary
    resource URIs."""
    server = build_server()

    (reader,) = [
        tool
        for tool in query(server, lambda client: client.list_tools())
        if tool.name == "read_warehouse_resource"
    ]

    assert set(reader.inputSchema["properties"]) == {"resource"}
    assert reader.inputSchema["properties"]["resource"]["enum"] == [
        "schema",
        "metrics",
        "conventions",
    ]
    assert reader.inputSchema["required"] == ["resource"]


def test_execute_query_applies_the_row_limits_the_model_cannot_set():
    """The limits are this service's policy, so they are read from settings and
    kept out of the schema."""
    settings = get_settings()
    recorded = {}

    def record(_client, _sql, **kwargs):
        recorded.update(kwargs)
        return {"rows": [], "row_count": 0}

    server = build_server()

    with patch.object(server_module.tools, "execute_query", record):
        query(
            server,
            lambda client: client.call_tool("execute_query", {"sql": "SELECT 1"}),
        )

    assert recorded == {
        "default_limit": settings.default_row_limit,
        "max_limit": settings.max_row_limit,
        "limit": None,
    }

    (execute_query,) = [
        tool
        for tool in query(server, lambda client: client.list_tools())
        if tool.name == "execute_query"
    ]

    assert set(execute_query.inputSchema["properties"]) == {"sql", "limit"}


# ---------------------------------------------------------------------------
# What the components do once called
# ---------------------------------------------------------------------------


def test_tools_query_the_client_the_factory_was_given():
    client = MagicMock()
    client.query.return_value = SimpleNamespace(result_rows=[("dim_farm",)])

    server = build_server(client)

    result = query(
        server,
        lambda session: session.call_tool("list_tables", {"database": "urbangreen_dw"}),
    )

    assert result.data["tables"] == ["dim_farm"]


def test_resources_read_through_mcp_and_schema_uses_the_factory_client():
    client = MagicMock()
    client.query.return_value = SimpleNamespace(
        result_rows=[("dim_farm", "CREATE TABLE dim_farm (farm_id UInt64)")]
    )
    server = build_server(client)

    schema = query(server, lambda session: session.read_resource(SCHEMA_URI))
    metrics = query(server, lambda session: session.read_resource(METRICS_URI))
    conventions = query(server, lambda session: session.read_resource(CONVENTIONS_URI))

    assert "## `dim_farm`" in schema[0].text
    assert "Yield Efficiency" in metrics[0].text
    assert "ReplacingMergeTree" in conventions[0].text
    assert schema[0].mimeType == "text/markdown"
    assert metrics[0].mimeType == "text/markdown"
    assert conventions[0].mimeType == "text/markdown"
    client.query.assert_called_once()


def test_model_facing_reader_delegates_to_the_registered_resources():
    """The tool is a model-facing adapter, not a second implementation of the
    resource loaders."""
    client = MagicMock()
    client.query.return_value = SimpleNamespace(
        result_rows=[("dim_farm", "CREATE TABLE dim_farm (farm_id UInt64)")]
    )
    server = build_server(client)

    schema = query(
        server,
        lambda session: session.call_tool("read_warehouse_resource", {"resource": "schema"}),
    )
    metrics = query(
        server,
        lambda session: session.call_tool("read_warehouse_resource", {"resource": "metrics"}),
    )
    conventions = query(
        server,
        lambda session: session.call_tool("read_warehouse_resource", {"resource": "conventions"}),
    )

    assert "## `dim_farm`" in schema.data
    assert "Yield Efficiency" in metrics.data
    assert "ReplacingMergeTree" in conventions.data
    client.query.assert_called_once()


def test_live_schema_is_cached_per_server():
    client = MagicMock()
    client.query.return_value = SimpleNamespace(
        result_rows=[("dim_farm", "CREATE TABLE dim_farm (farm_id UInt64)")]
    )
    server = build_server(client)

    query(
        server,
        lambda session: session.call_tool("read_warehouse_resource", {"resource": "schema"}),
    )
    query(server, lambda session: session.read_resource(SCHEMA_URI))

    client.query.assert_called_once()


def test_prompts_render_as_user_messages_through_mcp():
    """A prompt is filled in by the user and starts the conversation. Rendering
    it as anything else would make it an instruction the model attributes to
    the server."""
    server = build_server()

    analyze_result = query(
        server,
        lambda client: client.get_prompt("analyze_metric", {"metric": "Energy Efficiency"}),
    )
    compare_result = query(
        server,
        lambda client: client.get_prompt(
            "compare_farms",
            {"farm_ids": [1, 2], "dimension": "yield", "days": 30},
        ),
    )
    anomaly_result = query(
        server,
        lambda client: client.get_prompt(
            "investigate_anomaly",
            {"farm_id": 1, "sensor_type": "Temperature", "days": 7},
        ),
    )

    (analyze_message,) = analyze_result.messages
    (compare_message,) = compare_result.messages
    (anomaly_message,) = anomaly_result.messages

    assert analyze_message.role == "user"
    assert "Energy Efficiency" in analyze_message.content.text
    assert compare_message.role == "user"
    assert "farms 1, 2" in compare_message.content.text
    assert anomaly_message.role == "user"
    assert "Temperature" in anomaly_message.content.text


# ---------------------------------------------------------------------------
# Plain HTTP routes
# ---------------------------------------------------------------------------


def get_route(server, path: str) -> httpx.Response:
    """Send a GET to a custom route through the server's ASGI app."""

    async def request():
        transport = httpx.ASGITransport(app=server.http_app())

        async with httpx.AsyncClient(transport=transport, base_url="http://mcp") as http:
            return await http.get(path)

    return asyncio.run(request())


def test_health_answers_without_touching_the_warehouse():
    """Compose polls this endpoint, and it reports whether the server is up -
    not whether ClickHouse is."""
    client = MagicMock()

    response = get_route(build_server(client), "/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    client.query.assert_not_called()


def test_metrics_route_exposes_tool_metrics_in_prometheus_format():
    response = get_route(build_server(), "/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "mcp_tool_calls_total" in response.text
    assert "mcp_tool_duration_seconds" in response.text
