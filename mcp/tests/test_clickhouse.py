from unittest.mock import MagicMock, patch

from app.clickhouse import get_clickhouse_client


@patch("app.clickhouse.clickhouse_connect.get_client")
@patch("app.clickhouse.get_settings")
def test_get_clickhouse_client(mock_get_settings, mock_get_client):
    settings = MagicMock(
        clickhouse_host="test-clickhouse",
        clickhouse_http_port=8123,
        clickhouse_user="test-user",
        clickhouse_password="test-password",
        clickhouse_db="test_db",
        clickhouse_query_timeout=15,
        clickhouse_memory_limit=512 * 1024 * 1024,
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
            "max_memory_usage": 512 * 1024 * 1024,
        },
    )
