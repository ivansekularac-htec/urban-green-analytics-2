"""Tests for the MCP application entry point."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.main import main


def test_main_starts_mcp_server_with_configured_settings():
    settings = SimpleNamespace(
        host="127.0.0.1",
        port=9000,
        log_level="INFO",
    )
    mcp = MagicMock()

    with (
        patch("app.main.get_settings", return_value=settings),
        patch("app.main.create_mcp_server", return_value=mcp) as create_mcp_server,
    ):
        main()

    create_mcp_server.assert_called_once_with()
    mcp.run.assert_called_once_with(
        transport="http",
        host="127.0.0.1",
        port=9000,
    )
