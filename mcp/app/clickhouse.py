from functools import lru_cache

import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import get_settings


@lru_cache
def get_clickhouse_client() -> Client:
    config = get_settings()

    return clickhouse_connect.get_client(
        host=config.clickhouse_host,
        port=config.clickhouse_port,
        username=config.clickhouse_username,
        password=config.clickhouse_password,
        database=config.clickhouse_database,
        settings={
            "readonly": 2,
            "max_execution_time": config.query_timeout_seconds,
            "max_memory_usage": config.query_max_memory_bytes,
        },
    )
