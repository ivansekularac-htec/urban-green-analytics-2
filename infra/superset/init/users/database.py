"""Shared database configuration for Superset bootstrap utilities."""

import os

import clickhouse_connect

CLICKHOUSE_CONFIG = {
    "host": os.environ["CLICKHOUSE_HOST"],
    "port": int(os.environ["CLICKHOUSE_HTTP_PORT"]),
    "database": os.environ["CLICKHOUSE_DB"],
    "username": os.environ["CLICKHOUSE_USER"],
    "password": os.environ["CLICKHOUSE_PASSWORD"],
}

SUPERSET_DATABASE_NAME = "Urban Green DW"


def get_clickhouse_client():
    """Return a ClickHouse client."""

    return clickhouse_connect.get_client(**CLICKHOUSE_CONFIG)


def get_sqlalchemy_uri():
    """Return the ClickHouse SQLAlchemy URI used by Superset."""

    return (
        f"clickhousedb://"
        f"{CLICKHOUSE_CONFIG['username']}:"
        f"{CLICKHOUSE_CONFIG['password']}@"
        f"{CLICKHOUSE_CONFIG['host']}:"
        f"{CLICKHOUSE_CONFIG['port']}/"
        f"{CLICKHOUSE_CONFIG['database']}"
    )
