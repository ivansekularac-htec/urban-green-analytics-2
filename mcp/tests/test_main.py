"""Tests for the MCP application entry point.

``mcp.run`` blocks forever, so it is mocked out: what matters here is that the
entry point hands it the transport and the settings it was given.
"""

from types import SimpleNamespace
from unittest.mock import patch

from app.main import main, mcp


def test_server_instance_is_named():
    """The FastMCP instance exists and carries the service name."""

    assert mcp.name == "urbangreen-mcp"


def test_main_starts_server_with_configured_settings():
    """main() runs the server over streamable-HTTP on the configured address."""

    settings = SimpleNamespace(mcp_host="127.0.0.1", mcp_port=9000)

    with (
        patch("app.main.get_settings", return_value=settings),
        patch("app.main.mcp.run") as run,
    ):
        main()

    run.assert_called_once_with(
        transport="http",
        host="127.0.0.1",
        port=9000,
    )
