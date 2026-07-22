"""Build Spark sessions configured for UTC and MinIO S3A access."""

from pyspark.sql import SparkSession

from .config import Settings


def build_spark_session(
    app_name: str,
    settings: Settings,
) -> SparkSession:
    endpoint = settings.minio_endpoint.rstrip("/")

    spark = (
        SparkSession.builder.appName(app_name)
        .config("spark.sql.session.timeZone", "UTC")
        .config(
            "spark.hadoop.fs.s3a.impl",
            "org.apache.hadoop.fs.s3a.S3AFileSystem",
        )
        .config(
            "spark.hadoop.fs.s3a.endpoint",
            endpoint,
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            settings.minio_user,
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            settings.minio_password,
        )
        .config(
            "spark.hadoop.fs.s3a.path.style.access",
            "true",
        )
        .config(
            "spark.hadoop.fs.s3a.connection.ssl.enabled",
            str(endpoint.startswith("https://")).lower(),
        )
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("WARN")

    return spark
