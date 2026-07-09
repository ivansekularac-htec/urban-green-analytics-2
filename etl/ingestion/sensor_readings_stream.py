"""Structured Streaming job for ingesting sensor readings from Kafka to MinIO.

Reads JSON messages from the sensor_readings Kafka topic, parses them with an
explicit schema matching the simulator payload, derives an event-date partition
from the event timestamp, and writes Parquet files to MinIO via S3A.
"""

from __future__ import annotations

import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, from_unixtime, to_date
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    LongType,
    StructField,
    StructType,
)

SENSOR_SCHEMA = StructType(
    [
        StructField("farm_sensor_id", IntegerType(), nullable=False),
        StructField("farm_id", IntegerType(), nullable=False),
        StructField("sensor_type_id", IntegerType(), nullable=False),
        StructField("value", DoubleType(), nullable=False),
        StructField("timestamp", LongType(), nullable=False),
    ]
)


def env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def build_spark_session() -> SparkSession:
    minio_api_port = env("MINIO_API_PORT", "9000")
    minio_endpoint = f"http://urbangreen-minio:{minio_api_port}"
    minio_access_key = env("MINIO_ROOT_USER", "minioadmin")
    minio_secret_key = env("MINIO_ROOT_PASSWORD", "minioadmin")

    return (
        SparkSession.builder.appName("sensor-readings-stream")
        .config("spark.sql.streaming.schemaInference", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint)
        .config("spark.hadoop.fs.s3a.access.key", minio_access_key)
        .config("spark.hadoop.fs.s3a.secret.key", minio_secret_key)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .getOrCreate()
    )


def main() -> None:
    kafka_bootstrap_servers = env(
        "SIMULATOR_KAFKA_BOOTSTRAP",
        "urbangreen-kafka:9092",
    )
    kafka_topic = env(
        "KAFKA_TOPIC_SENSOR_READINGS",
        "sensor_readings",
    )
    kafka_starting_offsets = env("KAFKA_STARTING_OFFSETS", "earliest")

    minio_staging_bucket = env("MINIO_STAGING_BUCKET", "staging")
    trigger_interval = env("STREAM_TRIGGER_INTERVAL", "60 seconds")

    output_path = f"s3a://{minio_staging_bucket}/raw/kafka/{kafka_topic}/"
    checkpoint_path = f"s3a://{minio_staging_bucket}/_checkpoints/kafka/{kafka_topic}/"

    spark = build_spark_session()
    spark.sparkContext.setLogLevel(env("SPARK_LOG_LEVEL", "INFO"))

    kafka_stream = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", kafka_topic)
        .option("startingOffsets", kafka_starting_offsets)
        .option("failOnDataLoss", "false")
        .load()
    )

    parsed_stream = (
        kafka_stream.select(
            from_json(col("value").cast("string"), SENSOR_SCHEMA).alias("payload")
        )
        .select("payload.*")
        .withColumn("event_date", to_date(from_unixtime(col("timestamp"))))
    )

    query = (
        parsed_stream.writeStream.format("parquet")
        .option("path", output_path)
        .option("checkpointLocation", checkpoint_path)
        .outputMode("append")
        .partitionBy("event_date")
        .trigger(processingTime=trigger_interval)
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
