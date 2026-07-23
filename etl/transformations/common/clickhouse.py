"""ClickHouse JDBC read/write helpers.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse
"""

from __future__ import annotations

from pyspark.sql import DataFrame, SparkSession

from common.constants import (
    CLICKHOUSE_JDBC_DRIVER,
    CLICKHOUSE_JDBC_URL,
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_USER,
)


def read_sql(spark: SparkSession, sql: str) -> DataFrame:
    """Run SQL on ClickHouse and return the result as a DataFrame.

    Prefer server-side filters and ``FINAL`` in ``sql`` so Spark does not
    pull unnecessary rows.
    """
    return (
        spark.read.format("jdbc")
        .option("url", CLICKHOUSE_JDBC_URL)
        .option("driver", CLICKHOUSE_JDBC_DRIVER)
        .option("user", CLICKHOUSE_USER)
        .option("password", CLICKHOUSE_PASSWORD)
        .option("dbtable", f"({sql}) AS sub")
        .load()
    )


def write_table(df: DataFrame, table: str) -> None:
    """Append a DataFrame to a ClickHouse table via JDBC."""
    (
        df.write.format("jdbc")
        .mode("append")
        .option("url", CLICKHOUSE_JDBC_URL)
        .option("driver", CLICKHOUSE_JDBC_DRIVER)
        .option("user", CLICKHOUSE_USER)
        .option("password", CLICKHOUSE_PASSWORD)
        .option("dbtable", table)
        .option("batchsize", "50000")
        .save()
    )
