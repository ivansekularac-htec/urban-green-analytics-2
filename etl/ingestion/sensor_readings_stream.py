"""Structured Streaming: sensor_readings (Kafka JSON) -> Parquet on MinIO (S3A).

Reads the ``sensor_readings`` Kafka topic, parses each JSON payload with an
explicit schema (no inference), drops rows that failed to parse, derives an
event-date partition column from the payload's UTC timestamp, and writes Parquet
to the MinIO staging bucket partitioned by that date.

The schema mirrors the simulator's Kafka payload exactly (not the Postgres column
names); ``from_json`` matches by JSON key, so any drift would silently yield
nulls. Mapping ``farm_sensor_id`` to the DB ``sensors.id`` happens downstream.

Config is read from the environment so the same script runs unchanged across
environments; the defaults target the compose stack.
"""

import logging
import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json, from_unixtime, to_date
from pyspark.sql.streaming import StreamingQueryListener
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    LongType,
    StructField,
    StructType,
)

logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP = os.environ.get("SIMULATOR_KAFKA_BOOTSTRAP", "urbangreen-kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC_SENSOR_READINGS", "sensor_readings")
STARTING_OFFSETS = os.environ.get("STREAM_STARTING_OFFSETS", "earliest")
TRIGGER_INTERVAL = os.environ.get("STREAM_TRIGGER_INTERVAL", "60 seconds")

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://urbangreen-minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "")
STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")

OUTPUT_PATH = f"s3a://{STAGING_BUCKET}/raw/kafka/{KAFKA_TOPIC}/"
CHECKPOINT_PATH = f"s3a://{STAGING_BUCKET}/_checkpoints/kafka/{KAFKA_TOPIC}/"

SENSOR_SCHEMA = StructType(
    [
        StructField("farm_sensor_id", IntegerType()),
        StructField("farm_id", IntegerType()),
        StructField("sensor_type_id", IntegerType()),
        StructField("value", DoubleType()),
        StructField("timestamp", LongType()),
    ]
)


class BatchLogger(StreamingQueryListener):
    """Logs streaming lifecycle and batch progress."""

    def onQueryStarted(self, event):
        """Log query start."""
        logger.info(f"stream started; query id={event.id}")

    def onQueryProgress(self, event):
        """Log completed micro-batches."""
        logger.info(
            f"Batch: {event.progress.batchId}, inputRows={event.progress.numInputRows}"
        )

    def onQueryTerminated(self, event):
        """Log query termination."""
        logger.info(f"stream terminated; query id={event.id}")


def build_spark():
    """SparkSession wired to MinIO via S3A, with streaming schema inference off.

    The session timezone is pinned to UTC so ``event_date`` is derived in UTC
    (matching the producer's epoch) regardless of the container timezone.
    """
    return (
        SparkSession.builder.appName("sensor_readings_stream")
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config("spark.sql.streaming.schemaInference", "false")
        .config("spark.sql.session.timeZone", "UTC")
        .getOrCreate()
    )


def read_source(spark):
    """Open the Kafka source stream. failOnDataLoss=false survives topic rebuilds."""
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", STARTING_OFFSETS)
        .option("failOnDataLoss", "false")
        .load()
    )


def parse(raw):
    """Decode the JSON value, drop unparseable rows, and add the event_date column."""
    decoded = raw.select(
        from_json(col("value").cast("string"), SENSOR_SCHEMA).alias("payload")
    ).select("payload.*")
    valid = decoded.filter(col("farm_sensor_id").isNotNull())
    return valid.withColumn("event_date", to_date(from_unixtime(col("timestamp"))))


def sink(events):
    """Start the Parquet writer: append mode, partitioned by event_date, checkpointed."""
    return (
        events.writeStream.format("parquet")
        .option("path", OUTPUT_PATH)
        .option("checkpointLocation", CHECKPOINT_PATH)
        .partitionBy("event_date")
        .outputMode("append")
        .trigger(processingTime=TRIGGER_INTERVAL)
        .start()
    )


def main():
    """Start the streaming pipeline and wait for termination."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )
    logging.getLogger("py4j").setLevel(logging.WARNING)

    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")
    spark.streams.addListener(BatchLogger())
    query = sink(parse(read_source(spark)))
    query.awaitTermination()


if __name__ == "__main__":
    main()
