"""Tests for the ClickHouse client factory."""

from unittest.mock import MagicMock, patch

from app.clickhouse import get_client
from app.config import get_settings


def test_get_client_passes_readonly_session_settings(monkeypatch):
    get_settings.cache_clear()
    get_client.cache_clear()

    monkeypatch.setenv("MCP_QUERY_TIMEOUT_SECONDS", "15")
    monkeypatch.setenv("MCP_QUERY_MAX_MEMORY_BYTES", "1048576")

    get_settings.cache_clear()

    fake = MagicMock()
    with patch("app.clickhouse.clickhouse_connect.get_client", return_value=fake) as mock_get:
        client = get_client()

    assert client is fake
    kwargs = mock_get.call_args.kwargs
    assert kwargs["connect_timeout"] == 10
    assert kwargs["send_receive_timeout"] == 20  # 15 + 5 headroom
    assert kwargs["autogenerate_session_id"] is False
    assert kwargs["settings"]["readonly"] == 2
    assert kwargs["settings"]["max_execution_time"] == 15
    assert kwargs["settings"]["max_memory_usage"] == 1_048_576

    get_client.cache_clear()
    get_settings.cache_clear()
