"""Tests for the ClickHouse client configuration."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import app.clickhouse as clickhouse


def test_clickhouse_client_uses_configured_settings():
    settings = SimpleNamespace(
        clickhouse_host="clickhouse.example.com",
        clickhouse_port=8124,
        clickhouse_db="test_dw",
        clickhouse_user="test_user",
        clickhouse_password="test_password",
        query_timeout_seconds=60,
        query_max_memory_bytes=268435456,
    )

    client = object()
    clickhouse._clickhouse_client = None

    with (
        patch("app.clickhouse.get_settings", return_value=settings),
        patch(
            "app.clickhouse.clickhouse_connect.get_client",
            return_value=client,
        ) as get_client,
    ):
        result = clickhouse.get_clickhouse_client()

    assert result is client

    get_client.assert_called_once_with(
        host="clickhouse.example.com",
        port=8124,
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

    clickhouse._clickhouse_client = None


def test_get_clickhouse_client_returns_same_instance():
    settings = SimpleNamespace(
        clickhouse_host="localhost",
        clickhouse_port=8123,
        clickhouse_db="test_dw",
        clickhouse_user="test",
        clickhouse_password="test",
        query_timeout_seconds=30,
        query_max_memory_bytes=536_870_912,
    )

    client = object()
    clickhouse._clickhouse_client = None

    with (
        patch("app.clickhouse.get_settings", return_value=settings),
        patch(
            "app.clickhouse.clickhouse_connect.get_client",
            return_value=client,
        ) as get_client,
    ):
        first = clickhouse.get_clickhouse_client()
        second = clickhouse.get_clickhouse_client()

    assert first is second
    get_client.assert_called_once()

    clickhouse._clickhouse_client = None


def test_close_clickhouse_client_closes_and_clears_instance():
    client = MagicMock()
    clickhouse._clickhouse_client = client

    clickhouse.close_clickhouse_client()

    client.close.assert_called_once()
    assert clickhouse._clickhouse_client is None
