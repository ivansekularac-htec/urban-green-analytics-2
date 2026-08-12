"""ClickHouse client configuration for the MCP service."""

from functools import lru_cache

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import get_settings


@lru_cache
def get_clickhouse_client() -> Client:
    """Return a cached ClickHouse client with enforced read-only query limits."""
    settings = get_settings()

    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_http_port,
        database=settings.clickhouse_db,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password.get_secret_value(),
        autogenerate_session_id=False,
        settings={
            "readonly": 2,
            "max_execution_time": settings.clickhouse_query_timeout,
            "max_memory_usage": settings.clickhouse_max_memory_usage,
        },
    )
