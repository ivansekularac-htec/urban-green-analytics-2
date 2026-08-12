import clickhouse_connect
from clickhouse_connect.driver.client import Client

from app.config import get_settings


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
            "max_execution_time": config.clickhouse_query_timeout_seconds,
            "max_memory_usage": config.clickhouse_max_memory_usage,
        },
    )
