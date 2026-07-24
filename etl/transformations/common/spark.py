"""SparkSession construction and raw-zone reads for the warehouse loaders."""

import logging

from pyspark.sql import SparkSession
from pyspark.sql.utils import AnalysisException

from common import config

logger = logging.getLogger(__name__)


def build_spark(app_name):
    """Build a session wired to MinIO over S3A.

    The master is intentionally not set here so the same script runs against the
    standalone cluster or locally, depending on what spark-submit passes.
    """
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.hadoop.fs.s3a.endpoint", config.MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", config.MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", config.MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def read_raw_postgres(spark, table):
    """Read every extracted slice of a flat Postgres table from the raw zone.

    The extractor writes one folder per run window, so the glob picks up all of
    them; de-duplication to a single current row per key is the loader's job.
    Returns None when the extractor has not produced anything yet.
    """
    path = f"{config.RAW_POSTGRES_PREFIX}/{table}/*/{table}.parquet"
    try:
        df = spark.read.parquet(path)
    except AnalysisException:
        logger.warning(f"no raw data for {table} at {path}")
        return None
    return df


def read_raw_postgres_partitioned(spark, table):
    """Read a day-partitioned Postgres extract from the raw zone.

    Layout: <table>/<run_window>/<partition_label>=<day>/<table>__partNNNN.parquet.
    The wildcard reaches every part file across all run windows and days. It is
    matched explicitly rather than by partition discovery: the run-window level
    is not a key=value directory, so discovery would misread it, and the
    partition day is derived in the loader from the event timestamp anyway.
    Returns None when nothing has been extracted yet.
    """
    path = f"{config.RAW_POSTGRES_PREFIX}/{table}/*/*/*.parquet"
    try:
        df = spark.read.parquet(path)
    except AnalysisException:
        logger.warning(f"no raw data for {table} at {path}")
        return None
    return df


def read_raw_kafka(spark, topic):
    """Read the streaming sink output for a Kafka topic from the raw zone.

    The streaming job partitions by event_date, so partition discovery is left
    on and event_date comes back as a column. Returns None when the stream has
    not written anything yet.
    """
    path = f"{config.RAW_KAFKA_PREFIX}/{topic}"
    try:
        df = spark.read.parquet(path)
    except AnalysisException:
        logger.warning(f"no raw data for topic {topic} at {path}")
        return None
    return df
