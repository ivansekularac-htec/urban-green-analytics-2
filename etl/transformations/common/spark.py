"""SparkSession factory for warehouse loaders.

Ticket: T3.3.1 — Build Spark Jobs that Populate the Warehouse
"""

from __future__ import annotations

from pyspark.sql import SparkSession

from common.constants import (
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
)


def build_spark(app_name: str) -> SparkSession:
    """Create a SparkSession wired to MinIO via S3A, with UTC session timezone.

    Master, driver host, and memory are left to ``spark-submit`` (or the future
    Airflow DAG) so this layer stays submit-agnostic.
    """
    return (
        SparkSession.builder.appName(app_name)
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )
