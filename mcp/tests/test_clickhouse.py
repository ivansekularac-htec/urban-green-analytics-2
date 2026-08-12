"""Tests for the ClickHouse client configuration."""

from types import SimpleNamespace
from unittest.mock import patch

from app.clickhouse import get_clickhouse_client


def test_clickhouse_client_uses_configured_settings():
    settings = SimpleNamespace(
        clickhouse_host="clickhouse.example.com",
        clickhouse_port=8123,
        clickhouse_db="test_dw",
        clickhouse_user="test_user",
        clickhouse_password="test_password",
        clickhouse_query_timeout_seconds=60,
        clickhouse_max_memory_usage=268435456,
    )

    client = object()

    get_clickhouse_client.cache_clear()

    with (
        patch("app.clickhouse.get_settings", return_value=settings),
        patch("app.clickhouse.clickhouse_connect.get_client", return_value=client) as get_client,
    ):
        result = get_clickhouse_client()

    assert result is client

    get_client.assert_called_once_with(
        host="clickhouse.example.com",
        port=8123,
        username="test_user",
        password="test_password",
        database="test_dw",
        autogenerate_session_id=False,
        settings={
            "readonly": 2,
            "max_execution_time": 60,
            "max_memory_usage": 268435456,
        },
    )

    get_clickhouse_client.cache_clear()


def test_get_clickhouse_client_returns_cached_instance():
    settings = SimpleNamespace(
        clickhouse_host="localhost",
        clickhouse_port=8123,
        clickhouse_db="test_dw",
        clickhouse_user="test",
        clickhouse_password="test",
        clickhouse_query_timeout_seconds=30,
        clickhouse_max_memory_usage=536_870_912,
    )

    client = object()

    get_clickhouse_client.cache_clear()

    with (
        patch("app.clickhouse.get_settings", return_value=settings),
        patch(
            "app.clickhouse.clickhouse_connect.get_client",
            return_value=client,
        ) as get_client,
    ):
        first = get_clickhouse_client()
        second = get_clickhouse_client()

    assert first is second
    get_client.assert_called_once()

    get_clickhouse_client.cache_clear()
