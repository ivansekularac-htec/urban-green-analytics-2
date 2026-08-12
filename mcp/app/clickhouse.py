"""Provides a ClickHouse client for the MCP service."""

from functools import lru_cache

import clickhouse_connect
from clickhouse_connect.driver import Client

from app.config import get_settings


@lru_cache
def get_clickhouse_client() -> Client:
    """Configure the cached client for read-only analytical queries."""
    settings = get_settings()

    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_http_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_db,
        settings={
            "readonly": 2,
            "max_execution_time": settings.clickhouse_query_timeout,
            "max_memory_usage": settings.clickhouse_memory_limit,
        },
    )
