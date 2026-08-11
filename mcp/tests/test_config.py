"""Tests for application configuration."""

from app.config import Settings, get_settings


def test_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "127.0.0.1")
    monkeypatch.setenv("MCP_PORT", "9000")

    settings = Settings()

    assert settings.host == "127.0.0.1"
    assert settings.port == 9000


def test_settings_use_default_values(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)

    settings = Settings()

    assert settings.host == "0.0.0.0"
    assert settings.port == 8001


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
