"""Provides a pre-configured read-only ClickHouse client for the MCP service."""

import clickhouse_connect
from clickhouse_connect.driver import Client

from app.config import get_settings


def get_clickhouse_client() -> Client:
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
