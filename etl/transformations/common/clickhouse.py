from pyspark.sql import DataFrame, SparkSession

from common.config import WarehouseSettings

CLICKHOUSE_JDBC_DRIVER = "com.clickhouse.jdbc.ClickHouseDriver"


def read_clickhouse_query(
    spark: SparkSession,
    settings: WarehouseSettings,
    query: str,
) -> DataFrame:
    """Read a ClickHouse query as a Spark DataFrame."""

    return (
        spark.read.format("jdbc")
        .option("url", settings.clickhouse_jdbc_url)
        .option("query", query)
        .option("user", settings.clickhouse_user)
        .option("password", settings.clickhouse_password)
        .option("driver", CLICKHOUSE_JDBC_DRIVER)
        .load()
    )


def write_clickhouse_table(
    dataframe: DataFrame,
    settings: WarehouseSettings,
    table_name: str,
) -> None:
    """Append a Spark DataFrame to an existing ClickHouse table."""

    full_table_name = f"{settings.clickhouse_database}.{table_name}"

    (
        dataframe.coalesce(settings.jdbc_write_partitions)
        .write.format("jdbc")
        .option("url", settings.clickhouse_jdbc_url)
        .option("dbtable", full_table_name)
        .option("user", settings.clickhouse_user)
        .option("password", settings.clickhouse_password)
        .option("driver", CLICKHOUSE_JDBC_DRIVER)
        .option(
            "batchsize",
            str(settings.jdbc_batch_size),
        )
        .mode("append")
        .save()
    )
