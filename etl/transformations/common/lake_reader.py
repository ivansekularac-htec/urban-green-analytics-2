"""Read raw PostgreSQL and Kafka Parquet datasets from MinIO."""

from pyspark.sql import DataFrame, SparkSession

from .config import Settings


def build_path(
    bucket: str,
    prefix: str,
    name: str,
) -> str:
    return f"s3a://{bucket.strip('/')}/{prefix.strip('/')}/{name.strip('/')}/"


def read_postgres_table(
    spark: SparkSession,
    settings: Settings,
    table_name: str,
) -> DataFrame:
    path = build_path(
        settings.minio_bucket,
        settings.postgres_raw_prefix,
        table_name,
    )

    return spark.read.option("recursiveFileLookup", "true").parquet(path)


def read_kafka_topic(
    spark: SparkSession,
    settings: Settings,
    topic_name: str,
) -> DataFrame:
    path = build_path(
        settings.minio_bucket,
        settings.kafka_raw_prefix,
        topic_name,
    )

    return spark.read.parquet(path)
