"""Smoke tests for the service configuration and server instance."""

from app.config import Settings, get_settings
from app.main import mcp


def test_settings_load_from_environment():
    """Settings are constructible from the environment set in conftest."""

    settings = Settings()

    assert settings.mcp_host == "127.0.0.1"
    assert settings.mcp_port == 8001


def test_get_settings_is_cached():
    """get_settings returns the same cached instance."""

    get_settings.cache_clear()

    assert get_settings() is get_settings()


def test_server_instance_is_named():
    """The FastMCP instance exists and carries the service name."""

    assert mcp.name == "urbangreen-mcp"
