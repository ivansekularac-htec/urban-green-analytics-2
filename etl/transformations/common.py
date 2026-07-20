"""Create a SparkSession configured for UrbanGreen transformation jobs.

The session is configured to:

- access MinIO via S3A
- use UTC for all timestamp operations
"""

import os

from pyspark.sql import DataFrame, SparkSession

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://urbangreen-minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "")


def create_spark(app_name: str) -> SparkSession:
    """Create a SparkSession configured for MinIO and ClickHouse loaders."""

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


# Read Parquet from MinIO
def read_parquet(spark: SparkSession, path: str) -> DataFrame:
    """Read Parquet data from MinIO."""
    return spark.read.parquet(path)


# Write DataFrame to ClickHouse

# shared constants if appropriate
