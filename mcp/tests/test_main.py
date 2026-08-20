"""Tests for the MCP application entry point."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.main import main


def test_main_builds_the_server_and_runs_it_with_configured_settings():
    """Logging has to be configured before the server is built, or the line the
    factory writes about what it registered is lost."""
    settings = SimpleNamespace(
        host="127.0.0.1",
        port=9000,
        log_level="INFO",
    )
    server = MagicMock()

    with (
        patch("app.main.get_settings", return_value=settings),
        patch("app.main.logging.basicConfig") as basic_config,
        patch("app.main.create_server", return_value=server) as create,
    ):
        main()

    create.assert_called_once_with()
    basic_config.assert_called_once_with(level="INFO")

    server.run.assert_called_once_with(
        transport="http",
        host="127.0.0.1",
        port=9000,
    )
