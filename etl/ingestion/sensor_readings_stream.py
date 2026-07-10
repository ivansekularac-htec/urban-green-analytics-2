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
import sys

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

KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "urbangreen-kafka:9092")
KAFKA_TOPIC = os.environ.get("KAFKA_TOPIC_SENSOR_READINGS", "sensor_readings")
STARTING_OFFSETS = os.environ.get("STREAM_STARTING_OFFSETS", "earliest")
TRIGGER_INTERVAL = os.environ.get("STREAM_TRIGGER_INTERVAL", "60 seconds")
LOG_LEVEL = os.environ.get("STREAM_LOG_LEVEL", "INFO").upper()

MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://urbangreen-minio:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_ROOT_PASSWORD", "")
STAGING_BUCKET = os.environ.get("MINIO_STAGING_BUCKET", "staging")

OUTPUT_PATH = f"s3a://{STAGING_BUCKET}/raw/kafka/{KAFKA_TOPIC}/"
CHECKPOINT_PATH = f"s3a://{STAGING_BUCKET}/_checkpoints/kafka/{KAFKA_TOPIC}/"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
    force=True,
)

logger = logging.getLogger(__name__)

SENSOR_SCHEMA = StructType(
    [
        StructField("farm_sensor_id", IntegerType()),
        StructField("farm_id", IntegerType()),
        StructField("sensor_type_id", IntegerType()),
        StructField("value", DoubleType()),
        StructField("timestamp", LongType()),
    ]
)


class BatchProgressListener(StreamingQueryListener):
    """Log the streaming query lifecycle and completed micro-batches."""

    def onQueryStarted(self, event) -> None:
        logger.info(f"stream started; query id={event.id}; run id={event.runId}")

    def onQueryProgress(self, event) -> None:
        progress = event.progress

        logger.info(
            f"Batch: {progress.batchId}; "
            f"input rows={progress.numInputRows}; "
            f"processed rows per second={progress.processedRowsPerSecond}"
        )

    def onQueryTerminated(self, event) -> None:
        if event.exception:
            logger.error(
                f"stream terminated; query id={event.id}; "
                f"run id={event.runId}; exception={event.exception}"
            )
            return

        logger.info(f"stream terminated; query id={event.id}; run id={event.runId}")

    def onQueryIdle(self, event) -> None:
        logger.debug(f"stream idle; query id={event.id}; run id={event.runId}")


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

    return valid.withColumn(
        "event_date",
        to_date(from_unixtime(col("timestamp"))),
    )


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
    """Wire source -> parse -> sink and block until the streaming query terminates."""
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")
    spark.streams.addListener(BatchProgressListener())

    logger.info(
        f"starting stream; topic={KAFKA_TOPIC}; "
        f"starting offsets={STARTING_OFFSETS}; "
        f"trigger interval={TRIGGER_INTERVAL}"
    )

    query = sink(parse(read_source(spark)))
    query.awaitTermination()


if __name__ == "__main__":
    main()
