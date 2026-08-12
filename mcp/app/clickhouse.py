"""Pre-configured ClickHouse client for the MCP service.

Every session this service opens is read-only. readonly=2 (rather than 1) is
deliberate: it permits SELECT and per-session setting changes - which the
timeout and memory caps below rely on - while still rejecting INSERT and DDL,
and a readonly session cannot lower readonly back to 0.

The client is shared, so it runs without a session id. ClickHouse serialises
requests that carry one, and two concurrent tool calls through a shared session
would fail with "Session is locked by a concurrent client". The read-only and
per-query settings travel with each request rather than with the session, so
dropping it costs nothing.
"""

from functools import lru_cache

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import get_settings


@lru_cache
def get_client() -> Client:
    """Return the shared read-only ClickHouse client.

    Cached so the process keeps one HTTP session instead of reconnecting on
    every call.
    """

    settings = get_settings()

    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_db,
        connect_timeout=settings.clickhouse_connect_timeout,
        send_receive_timeout=settings.clickhouse_query_timeout,
        autogenerate_session_id=False,
        settings={
            "readonly": 2,
            "max_execution_time": settings.clickhouse_query_timeout,
            "max_memory_usage": settings.clickhouse_max_memory_usage,
        },
    )
