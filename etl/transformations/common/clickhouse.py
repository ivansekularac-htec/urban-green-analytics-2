"""ClickHouse JDBC access for the warehouse loaders."""

import logging

from common import config

logger = logging.getLogger(__name__)

DRIVER = "com.clickhouse.jdbc.ClickHouseDriver"

JDBC_URL = (
    f"jdbc:clickhouse://{config.CLICKHOUSE_HOST}:{config.CLICKHOUSE_HTTP_PORT}"
    f"/{config.CLICKHOUSE_DB}"
)


def _properties():
    """Connection properties handed to the JDBC reader/writer."""
    return {
        "user": config.CLICKHOUSE_USER,
        "password": config.CLICKHOUSE_PASSWORD,
        "driver": DRIVER,
    }


def read_query(spark, query):
    """Run a SELECT in ClickHouse and return the result as a DataFrame.

    Reads of ReplacingMergeTree tables should collapse duplicates themselves
    (FINAL or argMax), because the background merge may not have run yet.
    """
    return spark.read.jdbc(
        url=JDBC_URL, table=f"({query}) AS subquery", properties=_properties()
    )


def table_exists(spark, table):
    """Return True when the table is present in the warehouse database."""
    query = (
        "SELECT count() AS matches FROM system.tables "
        f"WHERE database = '{config.CLICKHOUSE_DB}' AND name = '{table}'"
    )
    return read_query(spark, query).collect()[0]["matches"] > 0


def write_table(df, table, mode="append"):
    """Append a DataFrame to a warehouse table.

    Columns omitted from the DataFrame fall back to their DDL defaults, so a
    loader does not have to supply _loaded_at. Every target table is a
    ReplacingMergeTree, so re-writing the same rows collapses on merge instead
    of accumulating duplicates.

    Raises when the table is missing. The Spark JDBC writer would otherwise
    issue its own CREATE TABLE, inventing a schema that ignores the engine,
    sorting key and column types the init scripts define. The warehouse schema
    belongs to those scripts, so a missing table is a setup error to surface,
    not something a loader may silently create.
    """
    if not table_exists(df.sparkSession, table):
        raise RuntimeError(
            f"{config.CLICKHOUSE_DB}.{table} does not exist - run the "
            "ClickHouse init scripts before loading"
        )

    count = df.count()
    df.write.jdbc(url=JDBC_URL, table=table, mode=mode, properties=_properties())
    logger.info(f"wrote {count} row(s) -> {config.CLICKHOUSE_DB}.{table}")
    return count
