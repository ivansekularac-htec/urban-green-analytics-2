from functools import lru_cache

import clickhouse_connect

from app.config import get_settings


@lru_cache
def get_client():
    settings = get_settings()
    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_http_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_db,
        connect_timeout=10,
        send_receive_timeout=settings.mcp_query_timeout_seconds + 5,
        autogenerate_session_id=False,
        settings={
            "readonly": 2,
            "max_execution_time": settings.mcp_query_timeout_seconds,
            "max_memory_usage": settings.mcp_query_max_memory_bytes,
        },
    )
