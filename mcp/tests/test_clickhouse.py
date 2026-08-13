"""Tests for the read-only ClickHouse client factory."""

from types import SimpleNamespace
from unittest.mock import patch

from app.clickhouse import CLIENT_TIMEOUT_HEADROOM_SECONDS, get_client


def _settings() -> SimpleNamespace:
    return SimpleNamespace(
        clickhouse_host="localhost",
        clickhouse_port=8123,
        clickhouse_user="test",
        clickhouse_password="test",
        clickhouse_db="test",
        clickhouse_connect_timeout=10,
        query_timeout_seconds=30,
        query_max_memory_bytes=536_870_912,
        max_row_limit=1000,
    )


def _build_client():
    get_client.cache_clear()

    with (
        patch("app.clickhouse.get_settings", return_value=_settings()),
        patch("app.clickhouse.clickhouse_connect.get_client") as factory,
    ):
        client = get_client()

    get_client.cache_clear()

    return client, factory


def test_client_session_enforces_readonly_and_query_caps():
    _, factory = _build_client()

    factory.assert_called_once()
    settings = factory.call_args.kwargs["settings"]

    assert settings["readonly"] == 2
    assert settings["max_execution_time"] == 30
    assert settings["max_memory_usage"] == 536_870_912
    assert settings["max_result_rows"] == 1000


def test_client_timeout_has_headroom_over_the_server_limit():
    """The socket read timeout must outlive the server-side execution limit."""

    _, factory = _build_client()

    kwargs = factory.call_args.kwargs

    assert kwargs["connect_timeout"] == 10
    assert kwargs["send_receive_timeout"] == 30 + CLIENT_TIMEOUT_HEADROOM_SECONDS
    assert kwargs["send_receive_timeout"] > kwargs["settings"]["max_execution_time"]


def test_client_connects_with_configured_target():
    _, factory = _build_client()

    kwargs = factory.call_args.kwargs

    assert kwargs["host"] == "localhost"
    assert kwargs["port"] == 8123
    assert kwargs["username"] == "test"
    assert kwargs["database"] == "test"


def test_client_runs_without_a_session_id():
    """A shared client must not carry a session: ClickHouse serialises those."""

    _, factory = _build_client()

    assert factory.call_args.kwargs["autogenerate_session_id"] is False


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
