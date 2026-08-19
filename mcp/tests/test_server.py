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
from app.resources import CONVENTIONS_URI, METRICS_URI, SCHEMA_URI
from app.server import create_server


def build_server(client: MagicMock | None = None):
    """Build a fully registered server with no warehouse behind it."""

    return create_server(client=client or MagicMock())


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


def test_the_server_instructs_the_model_to_read_the_resources_first():
    """The instructions are the first thing a client says about this server,
    and naming the URIs is what makes them findable."""
    server = build_server()

    assert SCHEMA_URI in server.instructions
    assert METRICS_URI in server.instructions
    assert CONVENTIONS_URI in server.instructions


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


def test_prompts_render_as_a_user_message():
    """A prompt is filled in by the user and starts the conversation. Rendering
    it as anything else would make it an instruction the model attributes to
    the server."""
    server = build_server()

    result = query(
        server,
        lambda client: client.get_prompt("analyze_metric", {"metric": "Energy Efficiency"}),
    )

    (message,) = result.messages

    assert message.role == "user"
    assert "Energy Efficiency" in message.content.text


# ---------------------------------------------------------------------------
# /health
# ---------------------------------------------------------------------------


def get_health(server) -> httpx.Response:
    """Send a GET to /health through the server's ASGI app."""

    async def request():
        transport = httpx.ASGITransport(app=server.http_app())

        async with httpx.AsyncClient(transport=transport, base_url="http://mcp") as http:
            return await http.get("/health")

    return asyncio.run(request())


def test_health_answers_without_touching_the_warehouse():
    """Compose polls this endpoint, and it reports whether the server is up -
    not whether ClickHouse is."""
    client = MagicMock()

    response = get_health(build_server(client))

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
    client.query.assert_not_called()
