"""
Shared Spark utilities for warehouse transformation jobs.

Provides helpers for:
- creating Spark sessions configured for MinIO and ClickHouse
- reading raw parquet data from MinIO
- writing and reading ClickHouse tables
- common timestamp conversions
"""

import os

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.functions import from_unixtime

MINIO_ENDPOINT = os.environ.get(
    "MINIO_ENDPOINT",
    "http://urbangreen-minio:9000",
)

MINIO_ACCESS_KEY = os.environ.get(
    "MINIO_ROOT_USER",
    "minioadmin",
)

MINIO_SECRET_KEY = os.environ.get(
    "MINIO_ROOT_PASSWORD",
    "",
)

CLICKHOUSE_USER = os.environ.get(
    "CLICKHOUSE_USER",
    "urbangreen",
)

CLICKHOUSE_PASSWORD = os.environ.get(
    "CLICKHOUSE_PASSWORD",
    "",
)

CLICKHOUSE_JDBC_URL = os.environ.get(
    "CLICKHOUSE_JDBC_URL",
    "jdbc:clickhouse://urbangreen-clickhouse:8123/urbangreen_dw",
)


def create_spark(app_name: str) -> SparkSession:
    """
    Create a SparkSession configured for MinIO and ClickHouse loaders.
    """

    return (
        SparkSession.builder.appName(app_name)
        .config(
            "spark.hadoop.fs.s3a.endpoint",
            MINIO_ENDPOINT,
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            MINIO_ACCESS_KEY,
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            MINIO_SECRET_KEY,
        )
        .config(
            "spark.hadoop.fs.s3a.path.style.access",
            "true",
        )
        .config(
            "spark.hadoop.fs.s3a.connection.ssl.enabled",
            "false",
        )
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config(
            "spark.sql.session.timeZone",
            "UTC",
        )
        .getOrCreate()
    )


def read_parquet(
    spark: SparkSession,
    *paths: str,
) -> DataFrame:
    """
    Read parquet files from MinIO.
    """

    return spark.read.parquet(*paths)


def list_batches(
    spark: SparkSession,
    path: str,
) -> list[str]:
    """
    Return batch directory names under a MinIO path.

    Example:
        s3a://staging/raw/postgres/crops/

    Returns:
        [
            "19700101T000000Z__20260720T141148Z",
            "20260720T141148Z__20260721T083000Z",
        ]
    """

    jvm = spark.sparkContext._jvm
    conf = spark.sparkContext._jsc.hadoopConfiguration()

    uri = jvm.java.net.URI(path)

    fs = jvm.org.apache.hadoop.fs.FileSystem.get(
        uri,
        conf,
    )

    statuses = fs.listStatus(
        jvm.org.apache.hadoop.fs.Path(path),
    )

    return sorted(file.getPath().getName() for file in statuses if file.isDirectory())


def get_latest_batch_path(
    spark: SparkSession,
    path: str,
) -> str:
    """
    Return the latest available ingestion batch.

    Batch folders are timestamp ranges:
        start__end

    Sorting lexicographically gives chronological order.
    """

    batches = list_batches(
        spark,
        path,
    )

    if not batches:
        raise RuntimeError(f"No ingestion batches found in {path}")

    return batches[-1]


def read_latest_batch(
    spark: SparkSession,
    bucket: str,
    table_name: str,
) -> DataFrame:
    """
    Read the latest ingestion batch from MinIO.

    The batch contains records extracted since
    the previous successful ingestion run.
    """

    base_path = f"s3a://{bucket}/raw/postgres/{table_name}/"

    latest_batch = get_latest_batch_path(
        spark,
        base_path,
    )

    return read_parquet(
        spark,
        f"{base_path}{latest_batch}",
    )


def execute_clickhouse_sql(
    spark: SparkSession,
    sql: str,
):
    """
    Execute a SQL statement against ClickHouse using JDBC.
    """

    jvm = spark.sparkContext._jvm

    conn = jvm.java.sql.DriverManager.getConnection(
        CLICKHOUSE_JDBC_URL,
        CLICKHOUSE_USER,
        CLICKHOUSE_PASSWORD,
    )

    try:
        statement = conn.createStatement()
        statement.execute(sql)
        statement.close()
    finally:
        conn.close()


def write_clickhouse(
    df: DataFrame,
    table_name: str,
    mode: str = "append",
):
    """
    Write Spark DataFrame to ClickHouse using JDBC.
    """

    (
        df.write.format("jdbc")
        .option(
            "url",
            CLICKHOUSE_JDBC_URL,
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
        .mode(mode)
        .save()
    )


def read_clickhouse(
    spark: SparkSession,
    table_expression: str,
) -> DataFrame:
    """
    Read a ClickHouse table using JDBC.
    """

    return (
        spark.read.format("jdbc")
        .option(
            "url",
            CLICKHOUSE_JDBC_URL,
        )
        .option(
            "dbtable",
            table_expression,
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


def epoch_to_timestamp(column):
    """
    Convert Unix epoch seconds to Spark timestamp.
    """

    return from_unixtime(column).cast("timestamp")
