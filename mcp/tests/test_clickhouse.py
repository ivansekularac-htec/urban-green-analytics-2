"""Tests for the read-only ClickHouse client factory."""

from types import SimpleNamespace
from unittest.mock import patch

from app.clickhouse import get_client


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        clickhouse_host="localhost",
        clickhouse_port=8123,
        clickhouse_user="test",
        clickhouse_password="test",
        clickhouse_db="test",
        clickhouse_connect_timeout=10,
        clickhouse_query_timeout=30,
        clickhouse_max_memory_usage=1_000_000_000,
    )


def test_client_session_enforces_readonly_and_query_caps():
    get_client.cache_clear()

    with (
        patch("app.clickhouse.get_settings", return_value=_settings()),
        patch("app.clickhouse.clickhouse_connect.get_client") as factory,
    ):
        get_client()

    factory.assert_called_once()
    kwargs = factory.call_args.kwargs

    assert kwargs["settings"]["readonly"] == 2
    assert kwargs["settings"]["max_execution_time"] == 30
    assert kwargs["settings"]["max_memory_usage"] == 1_000_000_000
    assert kwargs["connect_timeout"] == 10
    assert kwargs["send_receive_timeout"] == 30

    get_client.cache_clear()


def test_client_runs_without_a_session_id():
    """A shared client must not carry a session: ClickHouse serialises those."""

    get_client.cache_clear()

    with (
        patch("app.clickhouse.get_settings", return_value=_settings()),
        patch("app.clickhouse.clickhouse_connect.get_client") as factory,
    ):
        get_client()

    assert factory.call_args.kwargs["autogenerate_session_id"] is False

    get_client.cache_clear()


def test_client_connects_with_configured_target():
    get_client.cache_clear()

    with (
        patch("app.clickhouse.get_settings", return_value=_settings()),
        patch("app.clickhouse.clickhouse_connect.get_client") as factory,
    ):
        get_client()

    kwargs = factory.call_args.kwargs

    assert kwargs["host"] == "localhost"
    assert kwargs["port"] == 8123
    assert kwargs["username"] == "test"
    assert kwargs["database"] == "test"

    get_client.cache_clear()


def test_get_client_returns_cached_instance():
    get_client.cache_clear()

    with (
        patch("app.clickhouse.get_settings", return_value=_settings()),
        patch("app.clickhouse.clickhouse_connect.get_client") as factory,
    ):
        first = get_client()
        second = get_client()

    assert first is second
    factory.assert_called_once()

    get_client.cache_clear()
