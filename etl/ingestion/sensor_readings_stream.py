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


def env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)

    if value is None or value == "":
        raise ValueError(f"Missing required environment variable: {name}")

    return value


def build_spark_session() -> SparkSession:
    minio_endpoint = env("MINIO_ENDPOINT", "http://urbangreen-minio:9000")
    minio_access_key = env("MINIO_ROOT_USER")
    minio_secret_key = env("MINIO_ROOT_PASSWORD")

    return (
        SparkSession.builder.appName("sensor-readings-stream")
        .config("spark.sql.streaming.schemaInference", "false")
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
        "KAFKA_BOOTSTRAP_SERVERS",
        "urbangreen-kafka:9092",
    )
    kafka_topic = env("KAFKA_TOPIC", "sensor_readings")
    kafka_starting_offsets = env("KAFKA_STARTING_OFFSETS", "latest")

    minio_staging_bucket = env("MINIO_STAGING_BUCKET")
    stream_trigger_interval = env("STREAM_TRIGGER_INTERVAL", "60 seconds")

    output_path = f"s3a://{minio_staging_bucket}/raw/kafka/{kafka_topic}/"
    checkpoint_path = f"s3a://{minio_staging_bucket}/_checkpoints/kafka/{kafka_topic}/"

    spark = build_spark_session()
    spark.sparkContext.setLogLevel("WARN")

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
            from_json(
                col("value").cast("string"),
                SENSOR_SCHEMA,
            ).alias("payload")
        )
        .select("payload.*")
        .withColumn(
            "event_date",
            to_date(from_unixtime(col("timestamp"))),
        )
    )

    query = (
        parsed_stream.writeStream.format("parquet")
        .outputMode("append")
        .option("path", output_path)
        .option("checkpointLocation", checkpoint_path)
        .partitionBy("event_date")
        .trigger(processingTime=stream_trigger_interval)
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
