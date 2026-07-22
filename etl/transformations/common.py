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
from pyspark.sql.functions import col, from_unixtime, row_number
from pyspark.sql.window import Window

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


def read_batches_since(
    spark: SparkSession,
    bucket: str,
    table_name: str,
    last_batch: str | None,
) -> tuple[DataFrame, str | None]:
    """
    Read every ingestion batch written after the supplied batch.

    Returns:
        dataframe,
        newest processed batch
    """

    base_path = f"s3a://{bucket}/raw/postgres/{table_name}/"

    batches = list_batches(
        spark,
        base_path,
    )

    if last_batch is None:
        batches_to_read = batches
    else:
        batches_to_read = [batch for batch in batches if batch > last_batch]

    if not batches_to_read:
        return (
            None,
            last_batch,
        )

    paths = [f"{base_path}{batch}" for batch in batches_to_read]

    return (
        read_parquet(
            spark,
            *paths,
        ),
        batches_to_read[-1],
    )


def read_incremental_sources(
    spark: SparkSession,
    bucket: str,
    state: dict | None,
    tables: list[str],
) -> dict[str, dict]:
    """
    Read new ingestion batches for multiple source tables.

    Each table is processed independently using its stored watermark.

    Returns:

    {
        "farms": {
            "df": DataFrame | None,
            "last_batch": str | None,
            "changed": bool,
        }
    }
    """

    sources = {}

    for table in tables:
        last_batch = None

        if state:
            last_batch = state.get(table)

        df, newest_batch = read_batches_since(
            spark,
            bucket,
            table,
            last_batch,
        )

        sources[table] = {
            "df": df,
            "last_batch": newest_batch,
            "changed": df is not None,
        }

    return sources


def read_current_snapshot(
    spark: SparkSession,
    bucket: str,
    table_name: str,
    primary_key: str = "id",
    version_column: str = "updated_at",
) -> DataFrame:
    """
    Reconstruct the current state of a source table.

    Airflow writes only changed rows to each batch. Reading only the latest
    batch therefore does not produce the current table state.

    This helper reads every batch and keeps the latest version of each
    primary key based on the version column.
    """

    base_path = f"s3a://{bucket}/raw/postgres/{table_name}/"

    paths = [
        f"{base_path}{batch}"
        for batch in list_batches(
            spark,
            base_path,
        )
    ]

    df = read_parquet(
        spark,
        *paths,
    )

    window = Window.partitionBy(
        primary_key,
    ).orderBy(
        col(version_column).desc(),
    )

    return (
        df.withColumn(
            "_row_number",
            row_number().over(window),
        )
        .filter(
            col("_row_number") == 1,
        )
        .drop("_row_number")
    )


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
