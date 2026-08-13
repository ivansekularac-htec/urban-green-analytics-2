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

    # _env_file=None ignores a developer's local .env, so this really tests the
    # defaults rather than whatever that file happens to hold.
    settings = Settings(_env_file=None)

    assert settings.host == "0.0.0.0"
    assert settings.port == 8001


def test_service_policy_loads_from_environment(monkeypatch):
    monkeypatch.setenv("MCP_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MCP_DEFAULT_ROW_LIMIT", "50")
    monkeypatch.setenv("MCP_MAX_ROW_LIMIT", "500")
    monkeypatch.setenv("MCP_QUERY_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("MCP_QUERY_MAX_MEMORY_BYTES", "1048576")

    settings = Settings()

    assert settings.log_level == "DEBUG"
    assert settings.default_row_limit == 50
    assert settings.max_row_limit == 500
    assert settings.query_timeout_seconds == 15
    assert settings.query_max_memory_bytes == 1_048_576


def test_service_policy_uses_default_values(monkeypatch):
    for var in (
        "MCP_LOG_LEVEL",
        "MCP_DEFAULT_ROW_LIMIT",
        "MCP_MAX_ROW_LIMIT",
        "MCP_QUERY_TIMEOUT_SECONDS",
        "MCP_QUERY_MAX_MEMORY_BYTES",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.log_level == "INFO"
    assert settings.default_row_limit == 100
    assert settings.max_row_limit == 1000
    assert settings.query_timeout_seconds == 30
    assert settings.query_max_memory_bytes == 536_870_912


def test_clickhouse_settings_load_from_environment(monkeypatch):
    monkeypatch.setenv("CLICKHOUSE_HOST", "localhost")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "9123")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "secret")

    settings = Settings()

    assert settings.clickhouse_host == "localhost"
    assert settings.clickhouse_port == 9123
    assert settings.clickhouse_password == "secret"


def test_clickhouse_settings_use_default_values(monkeypatch):
    for var in (
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_HTTP_PORT",
        "CLICKHOUSE_DB",
        "CLICKHOUSE_USER",
        "CLICKHOUSE_PASSWORD",
        "CLICKHOUSE_CONNECT_TIMEOUT",
    ):
        monkeypatch.delenv(var, raising=False)

    settings = Settings(_env_file=None)

    assert settings.clickhouse_host == "urbangreen-clickhouse"
    assert settings.clickhouse_port == 8123
    assert settings.clickhouse_db == "urbangreen_dw"
    assert settings.clickhouse_user == "urbangreen"
    assert settings.clickhouse_password == ""
    assert settings.clickhouse_connect_timeout == 10


def test_get_settings_returns_cached_instance():
    get_settings.cache_clear()

    assert get_settings() is get_settings()

    get_settings.cache_clear()
