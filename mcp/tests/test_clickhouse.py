from types import SimpleNamespace
from unittest.mock import patch

from app.clickhouse import get_clickhouse_client


def test_client_is_created_with_read_only_limits():
    config = SimpleNamespace(
        clickhouse_host="clickhouse",
        clickhouse_port=8123,
        clickhouse_database="analytics",
        clickhouse_username="reader",
        clickhouse_password="secret",
        clickhouse_query_timeout_seconds=30,
        clickhouse_max_memory_usage=536870912,
    )

    with (
        patch("app.clickhouse.get_settings", return_value=config),
        patch("app.clickhouse.clickhouse_connect.get_client") as create_client,
    ):
        client = get_clickhouse_client()

    assert client is create_client.return_value
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
