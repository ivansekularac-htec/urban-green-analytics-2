from pyspark.sql import DataFrame

from common.config import (
    CLICKHOUSE_PASSWORD,
    CLICKHOUSE_URL,
    CLICKHOUSE_USER,
)


def truncate_clickhouse_table(
    spark,
    table_name: str,
):
    """
    Removes all rows from an existing ClickHouse table.

    Executes a TRUNCATE TABLE statement through the ClickHouse JDBC
    connection obtained from the active Spark session. The table structure,
    schema, indexes, and engine configuration remain unchanged.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session used to access the JVM JDBC driver.

    table_name : str
        Fully qualified ClickHouse table name to truncate.
        Example:
            "urbangreen_dw.dim_role"

    Raises
    ------
    java.sql.SQLException
        If the ClickHouse connection fails or the target table does not exist.
    """

    connection = spark._jvm.java.sql.DriverManager.getConnection(
        CLICKHOUSE_URL,
        CLICKHOUSE_USER,
        CLICKHOUSE_PASSWORD,
    )

    statement = connection.createStatement()

    try:
        statement.execute(f"TRUNCATE TABLE {table_name}")
    finally:
        statement.close()
        connection.close()


def write_to_clickhouse(df, table_name, truncate=False):
    """
    Writes a Spark DataFrame into a ClickHouse table using JDBC.

    The function appends data into the target table by default. When
    ``truncate`` is enabled, all existing rows are removed before the insert
    operation while preserving the ClickHouse table definition.

    Parameters
    ----------
    df : DataFrame
        Spark DataFrame containing the records to be written.

    table_name : str
        Destination ClickHouse table name.
        Example:
            "urbangreen_dw.dim_role"

    truncate : bool, default=False
        Whether to remove existing table data before inserting new records.

    Raises
    ------
    java.sql.SQLException
        If truncation or JDBC write operation fails.
    """
    if truncate:
        truncate_clickhouse_table(df.sparkSession, table_name)

    (
        df.write.format("jdbc")
        .option("url", CLICKHOUSE_URL)
        .option("dbtable", table_name)
        .option("user", CLICKHOUSE_USER)
        .option("password", CLICKHOUSE_PASSWORD)
        .option("driver", "com.clickhouse.jdbc.ClickHouseDriver")
        .option("batchsize", "10000")
        .mode("append")
        .save()
    )


def read_clickhouse(
    spark,
    table_name: str,
) -> DataFrame:
    """
    Reads a ClickHouse table into a Spark DataFrame using JDBC.

    Loads the complete contents of the specified ClickHouse table while
    preserving the schema inferred by Spark from the JDBC metadata.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session used for executing the JDBC read operation.

    table_name : str
        Source ClickHouse table name.
        Example:
            "urbangreen_dw.dim_role"

    Returns
    -------
    DataFrame
        Spark DataFrame containing the data from the ClickHouse table.

    Raises
    ------
    java.sql.SQLException
        If the JDBC connection or read operation fails.
    """

    return (
        spark.read.format("jdbc")
        .option(
            "url",
            CLICKHOUSE_URL,
        )
        .option(
            "dbtable",
            table_name,
        )
        .option(
            "user",
            CLICKHOUSE_USER,
        )
        .option(
            "password",
            CLICKHOUSE_PASSWORD,
        )
        .option(
            "driver",
            "com.clickhouse.jdbc.ClickHouseDriver",
        )
        .load()
    )
