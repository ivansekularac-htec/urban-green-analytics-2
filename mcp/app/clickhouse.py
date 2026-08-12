import clickhouse_connect

from app.config import get_settings

_clickhouse_client = None


def get_clickhouse_client():
    global _clickhouse_client

    if _clickhouse_client is None:
        settings = get_settings()

        _clickhouse_client = clickhouse_connect.get_client(
            host=settings.clickhouse_host,
            port=settings.clickhouse_port,
            username=settings.clickhouse_user,
            password=settings.clickhouse_password,
            database=settings.clickhouse_db,
            autogenerate_session_id=False,
            settings={
                "readonly": 2,
                "max_execution_time": settings.query_timeout_seconds,
                "max_memory_usage": settings.query_max_memory_bytes,
            },
        )

    return _clickhouse_client


def close_clickhouse_client() -> None:
    global _clickhouse_client

    if _clickhouse_client is not None:
        _clickhouse_client.close()
        _clickhouse_client = None
