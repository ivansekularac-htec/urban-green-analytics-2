from functools import lru_cache

import clickhouse_connect

from app.config import get_settings


@lru_cache
def get_clickhouse_client():
    settings = get_settings()

    return clickhouse_connect.get_client(
        host=settings.clickhouse_host,
        port=settings.clickhouse_port,
        username=settings.clickhouse_user,
        password=settings.clickhouse_password,
        database=settings.clickhouse_db,
        autogenerate_session_id=False,
        settings={
            "readonly": 2,
            "max_execution_time": settings.clickhouse_query_timeout_seconds,
            "max_memory_usage": settings.clickhouse_max_memory_usage,
        },
    )


def close_clickhouse_client() -> None:
    if get_clickhouse_client.cache_info().currsize:
        get_clickhouse_client().close()
        get_clickhouse_client.cache_clear()
