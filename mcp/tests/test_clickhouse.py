from unittest.mock import MagicMock, patch

import pytest

from app.clickhouse import get_clickhouse_client


@pytest.fixture(autouse=True)
def clear_clickhouse_client_cache():
    """Clear the ClickHouse client cache before and after each test."""
    get_clickhouse_client.cache_clear()
    yield
    get_clickhouse_client.cache_clear()


@patch("app.clickhouse.clickhouse_connect.get_client")
@patch("app.clickhouse.get_settings")
def test_get_clickhouse_client(mock_get_settings, mock_get_client):
    """Verify that the client uses the configured connection and query settings."""
    settings = MagicMock(
        mcp_clickhouse_query_timeout=15,
        mcp_clickhouse_memory_limit=536_870_912,
        clickhouse_host="test-clickhouse",
        clickhouse_http_port=8123,
        clickhouse_user="test-user",
        clickhouse_password="test-password",
        clickhouse_db="test_db",
    )
    mock_get_settings.return_value = settings

    get_clickhouse_client()

    mock_get_client.assert_called_once_with(
        host="test-clickhouse",
        port=8123,
        username="test-user",
        password="test-password",
        database="test_db",
        settings={
            "readonly": 2,
            "max_execution_time": 15,
            "max_memory_usage": 536_870_912,
        },
    )


@patch("app.clickhouse.clickhouse_connect.get_client")
@patch("app.clickhouse.get_settings")
def test_get_clickhouse_client_returns_cached_instance(
    mock_get_settings,
    mock_get_client,
):
    """Verify that the ClickHouse client is created only once per process."""
    settings = MagicMock(
        mcp_clickhouse_query_timeout=30,
        mcp_clickhouse_memory_limit=536_870_912,
        clickhouse_host="test-clickhouse",
        clickhouse_http_port=8123,
        clickhouse_user="test-user",
        clickhouse_password="test-password",
        clickhouse_db="test_db",
    )
    mock_get_settings.return_value = settings

    client = MagicMock()
    mock_get_client.return_value = client

    first = get_clickhouse_client()
    second = get_clickhouse_client()

    assert first is second
    mock_get_client.assert_called_once()
