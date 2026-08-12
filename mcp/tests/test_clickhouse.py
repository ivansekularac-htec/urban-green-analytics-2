from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.clickhouse import get_clickhouse_client


@pytest.fixture(autouse=True)
def clear_clickhouse_client_cache():
    get_clickhouse_client.cache_clear()
    yield
    get_clickhouse_client.cache_clear()


def test_client_is_created_with_read_only_limits_and_cached():
    config = SimpleNamespace(
        clickhouse_host="clickhouse",
        clickhouse_port=8123,
        clickhouse_database="analytics",
        clickhouse_username="reader",
        clickhouse_password="secret",
        query_timeout_seconds=30,
        query_max_memory_bytes=536870912,
    )

    with (
        patch("app.clickhouse.get_settings", return_value=config),
        patch("app.clickhouse.clickhouse_connect.get_client") as create_client,
    ):
        client = get_clickhouse_client()
        cached_client = get_clickhouse_client()

    assert client is create_client.return_value
    assert cached_client is client

    create_client.assert_called_once_with(
        host="clickhouse",
        port=8123,
        username="reader",
        password="secret",
        database="analytics",
        settings={
            "readonly": 2,
            "max_execution_time": 30,
            "max_memory_usage": 536870912,
        },
    )
