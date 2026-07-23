from __future__ import annotations

from pyspark.sql import SparkSession

from common.config import WarehouseSettings


def create_spark_session(
    job_name: str,
    settings: WarehouseSettings,
) -> SparkSession:
    """Create the Spark session used by one warehouse loader."""

    spark = (
        SparkSession.builder.appName(job_name)
        .config("spark.sql.session.timeZone", "UTC")
        .config(
            "spark.hadoop.fs.s3a.endpoint",
            settings.minio_endpoint,
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            settings.minio_access_key,
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            settings.minio_secret_key,
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
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem",
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    return spark
