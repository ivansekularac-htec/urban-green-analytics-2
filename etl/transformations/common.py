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


def list_batches(spark: SparkSession, path: str) -> list[str]:
    """
    Return batch directory names under the given S3A path.

    Example:
        s3a://staging/raw/postgres/crops/

    returns:
        [
            "19700101T000000Z__20260720T141148Z",
            "20260720T141148Z__20260721T083000Z",
        ]
    """
    jvm = spark.sparkContext._jvm
    conf = spark.sparkContext._jsc.hadoopConfiguration()

    uri = jvm.java.net.URI(path)
    fs = jvm.org.apache.hadoop.fs.FileSystem.get(uri, conf)

    statuses = fs.listStatus(jvm.org.apache.hadoop.fs.Path(path))

    return sorted(file.getPath().getName() for file in statuses if file.isDirectory())


# Read Parquet from MinIO
def read_parquet(spark: SparkSession, path: str) -> DataFrame:
    """Read Parquet data from MinIO."""
    return spark.read.parquet(path)


# Write DataFrame to ClickHouse

# shared constants if appropriate
