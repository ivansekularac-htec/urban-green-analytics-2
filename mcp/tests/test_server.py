"""
Tests for the FastMCP server factory.

The factory is where the tool functions stop being pure and start being an API
the model can call, so what is asserted here is the shape of that API: which
names are registered, and which parameters the model is and is not asked to
fill. FastMCP's introspection is async, so each test drives it through
`asyncio.run` rather than adding a pytest plugin for one call.
"""

import asyncio
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app import server
from app.resources import CONVENTIONS_URI, METRICS_URI, SCHEMA_URI, conventions_resource

EXPECTED_TOOLS = {
    "read_resource",
    "get_prompt",
    "list_tables",
    "describe_table",
    "execute_query",
}
EXPECTED_RESOURCES = {SCHEMA_URI, METRICS_URI, CONVENTIONS_URI}
EXPECTED_PROMPTS = {"analyze_metric", "compare_farms", "investigate_anomaly"}

# The model must never be asked for these. `client` is not its to supply, and
# the two limits are the service's policy - offering them would let the model
# raise its own row ceiling.
FORBIDDEN_PARAMETERS = {"client", "default_limit", "max_limit"}


@pytest.fixture
def settings():
    return SimpleNamespace(
        clickhouse_db="urbangreen_dw",
        default_row_limit=100,
        max_row_limit=1000,
    )


@pytest.fixture
def build(settings):
    """Build a server against a client double, returning it with that client.

    The client is passed in rather than patched, which is the difference the
    factory's signature is there to make.
    """

    def _build(client: MagicMock | None = None):
        if client is None:
            client = MagicMock()
            client.query.return_value = SimpleNamespace(
                result_rows=[("dim_crop", "CREATE TABLE dim_crop (crop_id UInt64)")]
            )

        with patch("app.server.get_settings", return_value=settings):
            mcp = server.create_server(client)

        return mcp, client

    return _build


# ---------------------------------------------------------------------------
# What gets registered
# ---------------------------------------------------------------------------


def test_the_factory_registers_every_tool(build):
    mcp, _ = build()

    names = {tool.name for tool in asyncio.run(mcp.list_tools())}

    assert names == EXPECTED_TOOLS


def test_the_factory_registers_every_resource(build):
    mcp, _ = build()

    uris = {str(resource.uri) for resource in asyncio.run(mcp.list_resources())}

    assert uris == EXPECTED_RESOURCES


def test_the_factory_registers_every_prompt(build):
    mcp, _ = build()

    names = {prompt.name for prompt in asyncio.run(mcp.list_prompts())}

    assert names == EXPECTED_PROMPTS


def test_the_given_client_is_the_one_the_server_uses(build, settings):
    """Passing one has to mean no second connection is opened behind it."""
    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.server.get_client") as get_client,
    ):
        server.create_server(MagicMock())

    get_client.assert_not_called()


def test_a_server_built_without_a_client_opens_one(settings):
    """`main` builds it that way, so the fallback has to stay wired."""
    with (
        patch("app.server.get_settings", return_value=settings),
        patch("app.server.get_client", return_value=MagicMock()) as get_client,
    ):
        server.create_server()

    get_client.assert_called_once_with()


# ---------------------------------------------------------------------------
# Reaching a resource and a prompt through a tool
#
# Registering either is not enough for a model to use one: under MCP the client
# reads resources and the user picks prompts, and the clients this server is
# used with offer neither. These two tools are the channel that survives a
# tools-only client, so each has to serve what its registry serves.
# ---------------------------------------------------------------------------


def test_a_resource_is_readable_through_the_tool(build):
    mcp, _ = build()

    payload = asyncio.run(mcp.call_tool("read_resource", {"uri": CONVENTIONS_URI}))

    assert payload.structured_content["content"] == conventions_resource()


def test_every_registered_resource_is_served_by_the_tool(build):
    """The tool reads the registration rather than its own copy of the URIs."""
    mcp, _ = build()

    for uri in (METRICS_URI, CONVENTIONS_URI):
        payload = asyncio.run(mcp.call_tool("read_resource", {"uri": uri}))

        assert payload.structured_content["uri"] == uri
        assert payload.structured_content["content"]


def test_an_unknown_uri_comes_back_with_the_ones_that_are_served(build):
    """A guess costs one call, not the answer."""
    mcp, _ = build()

    payload = asyncio.run(mcp.call_tool("read_resource", {"uri": "urbangreen://nope"}))
    error = payload.structured_content["error"]

    for uri in EXPECTED_RESOURCES:
        assert uri in error


def test_the_schema_is_read_from_the_warehouse_once(build):
    """It is the one resource that costs a round trip, so it is cached."""
    mcp, client = build()

    first = asyncio.run(mcp.call_tool("read_resource", {"uri": SCHEMA_URI}))
    second = asyncio.run(mcp.call_tool("read_resource", {"uri": SCHEMA_URI}))

    assert first.structured_content == second.structured_content
    assert "dim_crop" in first.structured_content["content"]
    client.query.assert_called_once()


def test_a_second_server_reads_the_schema_again(build):
    """The cache belongs to the server, not to the process - otherwise one
    server's warehouse leaks into the next one built."""
    _, first_client = build()
    mcp, second_client = build()

    asyncio.run(mcp.call_tool("read_resource", {"uri": SCHEMA_URI}))

    second_client.query.assert_called_once()
    first_client.query.assert_not_called()


def test_a_prompt_is_rendered_through_the_tool(build):
    """The argument reaches the template, so the tool is not handing back the
    template's description in place of its output."""
    mcp, _ = build()

    payload = asyncio.run(
        mcp.call_tool(
            "get_prompt",
            {"name": "analyze_metric", "arguments": {"metric": "Energy Efficiency"}},
        )
    )
    rendered = payload.structured_content["prompt"]

    assert "Energy Efficiency" in rendered
    assert METRICS_URI in rendered


def test_a_prompt_renders_with_only_its_required_arguments(build):
    """`days` has a default, so the model is not forced to invent a window."""
    mcp, _ = build()

    payload = asyncio.run(
        mcp.call_tool(
            "get_prompt",
            {"name": "investigate_anomaly", "arguments": {"farm_id": 7, "sensor_type": "pH"}},
        )
    )

    assert payload.structured_content["name"] == "investigate_anomaly"
    assert payload.structured_content["prompt"]


def test_arguments_sent_as_json_text_render_the_same_prompt(build):
    """A client that flattens the nested schema sends the text, and the call
    carried everything needed - so it is answered rather than refused."""
    mcp, _ = build()

    as_object = asyncio.run(
        mcp.call_tool(
            "get_prompt",
            {"name": "analyze_metric", "arguments": {"metric": "Yield Efficiency"}},
        )
    )
    as_text = asyncio.run(
        mcp.call_tool(
            "get_prompt",
            {"name": "analyze_metric", "arguments": '{"metric": "Yield Efficiency"}'},
        )
    )

    assert as_text.structured_content == as_object.structured_content


def test_arguments_that_are_not_json_say_so(build):
    mcp, _ = build()

    payload = asyncio.run(
        mcp.call_tool("get_prompt", {"name": "analyze_metric", "arguments": "metric=yield"})
    )

    assert "not JSON" in payload.structured_content["error"]


def test_an_unknown_prompt_comes_back_with_the_ones_that_are_served(build):
    mcp, _ = build()

    payload = asyncio.run(mcp.call_tool("get_prompt", {"name": "summarise", "arguments": {}}))
    error = payload.structured_content["error"]

    for name in EXPECTED_PROMPTS:
        assert name in error


def test_an_argument_a_template_does_not_take_comes_back_with_the_ones_it_does(build):
    """Otherwise the model retries variations until the context is gone."""
    mcp, _ = build()

    payload = asyncio.run(
        mcp.call_tool("get_prompt", {"name": "analyze_metric", "arguments": {"metrics": "yield"}})
    )
    error = payload.structured_content["error"]

    assert "metric" in error
    assert "days" in error


# ---------------------------------------------------------------------------
# What the model is asked to fill
# ---------------------------------------------------------------------------


def test_no_tool_asks_the_model_for_a_dependency_or_a_limit(build):
    mcp, _ = build()

    for tool in asyncio.run(mcp.list_tools()):
        fields = set(tool.parameters.get("properties", {}))

        assert not fields & FORBIDDEN_PARAMETERS, tool.name


def test_execute_query_takes_the_sql_and_an_optional_limit(build):
    mcp, _ = build()

    tool = next(t for t in asyncio.run(mcp.list_tools()) if t.name == "execute_query")
    schema = tool.parameters

    assert set(schema["properties"]) == {"sql", "limit"}
    assert schema.get("required") == ["sql"]


def test_every_tool_carries_a_description_for_the_model(build):
    mcp, _ = build()

    for tool in asyncio.run(mcp.list_tools()):
        assert tool.description, tool.name


# ---------------------------------------------------------------------------
# Wiring the tools to the shared client and the configured limits
# ---------------------------------------------------------------------------


def test_the_tools_pass_the_shared_client_and_the_configured_limits(build, settings):
    client = MagicMock()
    mcp, _ = build(client)

    with patch("app.server.tools.execute_query", return_value={}) as execute_query:
        asyncio.run(mcp.call_tool("execute_query", {"sql": "SELECT 1"}))

    execute_query.assert_called_once_with(
        client,
        "SELECT 1",
        default_limit=settings.default_row_limit,
        max_limit=settings.max_row_limit,
        limit=None,
    )


def test_the_database_defaults_to_the_configured_one(build, settings):
    mcp, client = build()

    with patch("app.server.tools.list_tables", return_value={}) as list_tables:
        asyncio.run(mcp.call_tool("list_tables", {}))

    list_tables.assert_called_once_with(client, settings.clickhouse_db)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def test_building_the_server_reports_what_it_registered(build, caplog):
    with caplog.at_level(logging.INFO, logger="app.server"):
        build()

    assert "5 tool(s)" in caplog.text
    assert "3 resource(s)" in caplog.text
    assert "3 prompt(s)" in caplog.text


def test_a_swallowed_tool_error_reaches_the_log(caplog):
    """`execute_query` hands a ClickHouse failure back as a payload so the model
    can correct itself, which would otherwise leave no trace anywhere."""
    with caplog.at_level(logging.WARNING, logger="app.server"):
        payload = server._reported("execute_query", {"error": "Unknown identifier"})

    assert payload == {"error": "Unknown identifier"}
    assert "execute_query returned an error" in caplog.text
    assert "Unknown identifier" in caplog.text


def test_a_successful_payload_is_not_logged(caplog):
    with caplog.at_level(logging.WARNING, logger="app.server"):
        server._reported("list_tables", {"tables": []})

    assert not caplog.text


# ---------------------------------------------------------------------------
# Instructions and health
# ---------------------------------------------------------------------------


def test_the_instructions_send_the_model_to_every_resource():
    """The instructions are the first thing the model reads, and they are the
    only place that names all three resources together."""
    for uri in EXPECTED_RESOURCES:
        assert uri in server.INSTRUCTIONS


def test_the_instructions_name_the_tools_that_reach_a_resource_and_a_prompt():
    """A bare URI or prompt name is not actionable - the model can call neither
    `resources/read` nor `prompts/get`."""
    assert "read_resource" in server.INSTRUCTIONS
    assert "get_prompt" in server.INSTRUCTIONS


def test_the_instructions_name_every_prompt_the_server_serves():
    """`get_prompt` takes a name, and nothing else tells the model what it is."""
    for name in EXPECTED_PROMPTS:
        assert name in server.INSTRUCTIONS


def test_the_instructions_order_the_tool_flow():
    instructions = server.INSTRUCTIONS

    assert instructions.index("list_tables") < instructions.index("describe_table")
    assert instructions.index("describe_table") < instructions.index("execute_query")


def test_health_is_served_outside_the_mcp_endpoints(build):
    """Compose polls it, so it has to answer without an MCP handshake."""
    mcp, _ = build()

    routes = {route.path for route in mcp.http_app().routes if hasattr(route, "path")}

    assert "/health" in routes
