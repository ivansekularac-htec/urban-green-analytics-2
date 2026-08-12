"""Tests for the Urban Green MCP server."""

from types import SimpleNamespace
from unittest.mock import Mock

import app.server as server


def test_mcp_server_name() -> None:
    """Verify that the MCP server has the expected name."""
    assert server.mcp.name == "Urban Green MCP"


def test_main_starts_server_with_configured_settings(monkeypatch) -> None:
    """Verify that main starts FastMCP with configured HTTP settings."""
    settings = SimpleNamespace(
        mcp_host="127.0.0.1",
        mcp_port=9000,
    )
    run_mock = Mock()

    monkeypatch.setattr(server, "get_settings", lambda: settings)
    monkeypatch.setattr(server.mcp, "run", run_mock)

    server.main()

    run_mock.assert_called_once_with(
        transport="http",
        host="127.0.0.1",
        port=9000,
    )
