"""Tests for ClickHouse client configuration."""

from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from pydantic import SecretStr

import app.clickhouse as clickhouse
from app.config import Settings


@pytest.fixture(autouse=True)
def clear_clickhouse_client_cache():
    """Clear the ClickHouse client cache before and after each test."""
    clickhouse.get_clickhouse_client.cache_clear()
    yield
    clickhouse.get_clickhouse_client.cache_clear()


def test_clickhouse_client_uses_default_settings(monkeypatch):
    """Verify that the client uses default connection and query settings."""
    env_vars = [
        "CLICKHOUSE_HOST",
        "CLICKHOUSE_HTTP_PORT",
        "CLICKHOUSE_DB",
        "CLICKHOUSE_USER",
        "MCP_QUERY_TIMEOUT_SECONDS",
        "MCP_QUERY_MAX_MEMORY_BYTES",
    ]

    for env_var in env_vars:
        monkeypatch.delenv(env_var, raising=False)

    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")

    settings = Settings(_env_file=None)

    client_mock = Mock()
    get_client_mock = Mock(return_value=client_mock)

    monkeypatch.setattr(clickhouse, "get_settings", lambda: settings)
    monkeypatch.setattr(
        clickhouse.clickhouse_connect,
        "get_client",
        get_client_mock,
    )

    client = clickhouse.get_clickhouse_client()

    assert client is client_mock

    get_client_mock.assert_called_once_with(
        host="urbangreen-clickhouse",
        port=8123,
        database="urbangreen_dw",
        username="urbangreen",
        password="test_password",
        autogenerate_session_id=False,
        settings={
            "readonly": 2,
            "max_execution_time": 30,
            "max_memory_usage": 500_000_000,
        },
    )


def test_clickhouse_client_uses_environment_overrides(monkeypatch):
    """Verify that environment values override the ClickHouse defaults."""
    monkeypatch.setenv("CLICKHOUSE_HOST", "localhost")
    monkeypatch.setenv("CLICKHOUSE_HTTP_PORT", "9001")
    monkeypatch.setenv("CLICKHOUSE_DB", "test_db")
    monkeypatch.setenv("CLICKHOUSE_USER", "test_user")
    monkeypatch.setenv("CLICKHOUSE_PASSWORD", "test_password")
    monkeypatch.setenv("MCP_QUERY_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("MCP_QUERY_MAX_MEMORY_BYTES", "100000000")

    settings = Settings(_env_file=None)

    client_mock = Mock()
    get_client_mock = Mock(return_value=client_mock)

    monkeypatch.setattr(clickhouse, "get_settings", lambda: settings)
    monkeypatch.setattr(
        clickhouse.clickhouse_connect,
        "get_client",
        get_client_mock,
    )

    client = clickhouse.get_clickhouse_client()

    assert client is client_mock

    get_client_mock.assert_called_once_with(
        host="localhost",
        port=9001,
        database="test_db",
        username="test_user",
        password="test_password",
        autogenerate_session_id=False,
        settings={
            "readonly": 2,
            "max_execution_time": 15,
            "max_memory_usage": 100_000_000,
        },
    )


def test_get_clickhouse_client_returns_cached_instance(monkeypatch):
    """Verify that the ClickHouse client is created only once per process."""
    settings = SimpleNamespace(
        clickhouse_host="localhost",
        clickhouse_http_port=8123,
        clickhouse_db="test_db",
        clickhouse_user="test_user",
        clickhouse_password=SecretStr("test_password"),
        query_timeout_seconds=30,
        query_max_memory_bytes=500_000_000,
    )

    client_mock = Mock()
    get_client_mock = Mock(return_value=client_mock)

    monkeypatch.setattr(clickhouse, "get_settings", lambda: settings)
    monkeypatch.setattr(
        clickhouse.clickhouse_connect,
        "get_client",
        get_client_mock,
    )

    first = clickhouse.get_clickhouse_client()
    second = clickhouse.get_clickhouse_client()

    assert first is second
    assert first is client_mock
    get_client_mock.assert_called_once()
