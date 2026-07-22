"""Atomically replace ClickHouse tables through staging tables."""

from pyspark.sql import DataFrame

from .clickhouse import (
    execute_clickhouse_sql,
    table_name,
    write_clickhouse_table,
)
from .config import Settings


def full_refresh_table(
    dataframe: DataFrame,
    settings: Settings,
    target_table: str,
) -> None:
    if dataframe.isEmpty():
        raise ValueError(f"Refusing to replace {target_table} with empty data")

    staging_table = f"{target_table}__staging"

    target = table_name(settings, target_table)
    staging = table_name(settings, staging_table)

    execute_clickhouse_sql(
        settings,
        f"DROP TABLE IF EXISTS {staging} SYNC",
    )

    execute_clickhouse_sql(
        settings,
        f"CREATE TABLE {staging} AS {target}",
    )

    write_clickhouse_table(
        dataframe,
        settings,
        staging_table,
    )

    execute_clickhouse_sql(
        settings,
        f"EXCHANGE TABLES {target} AND {staging}",
    )

    execute_clickhouse_sql(
        settings,
        f"DROP TABLE IF EXISTS {staging} SYNC",
    )
