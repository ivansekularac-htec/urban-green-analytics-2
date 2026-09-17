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

import json
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
KAFKA_CONSUMER_GROUP = os.environ.get("KAFKA_CONSUMER_GROUP", "urbangreen-spark-streaming")
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
    """Log batch progress and mirror completed offsets for lag monitoring.

    Structured Streaming recovers from its checkpoint and deliberately does not
    commit source offsets to Kafka. kafka-exporter can only calculate consumer
    lag for committed groups, so completed end offsets are mirrored to a
    monitoring-only group after Spark has committed each output batch.
    """

    def __init__(self, jvm):
        """Create a Kafka Admin client from jars already loaded by Spark."""
        super().__init__()
        self._jvm = jvm
        properties = jvm.java.util.Properties()
        properties.put("bootstrap.servers", KAFKA_BOOTSTRAP)
        properties.put("client.id", "urbangreen-spark-offset-reporter")
        properties.put("default.api.timeout.ms", "10000")
        self._admin = jvm.org.apache.kafka.clients.admin.AdminClient.create(properties)

    def onQueryStarted(self, event):
        """Log query start."""
        logger.info(f"stream started; query id={event.id}")

    def onQueryProgress(self, event):
        """Log a completed micro-batch and publish its next Kafka offsets."""
        logger.info(f"Batch: {event.progress.batchId}, inputRows={event.progress.numInputRows}")
        try:
            self._commit_offsets(event.progress.sources)
        except Exception:
            # Monitoring must never stop the data pipeline. The next completed
            # batch retries with a newer offset and closes any temporary gap.
            logger.exception(
                "failed to mirror Kafka offsets for consumer group=%s",
                KAFKA_CONSUMER_GROUP,
            )

    def _commit_offsets(self, sources):
        """Commit Spark's completed end offsets to the monitoring consumer group."""
        java_offsets = self._jvm.java.util.HashMap()

        for source in sources:
            end_offset = source.get("endOffset") if isinstance(source, dict) else source.endOffset
            if not end_offset:
                continue

            for topic, partitions in json.loads(end_offset).items():
                for partition, offset in partitions.items():
                    topic_partition = self._jvm.org.apache.kafka.common.TopicPartition(
                        topic, int(partition)
                    )
                    offset_metadata = self._jvm.org.apache.kafka.clients.consumer.OffsetAndMetadata(
                        int(offset)
                    )
                    java_offsets.put(topic_partition, offset_metadata)

        if java_offsets.isEmpty():
            return

        self._admin.alterConsumerGroupOffsets(KAFKA_CONSUMER_GROUP, java_offsets).all().get(
            10, self._jvm.java.util.concurrent.TimeUnit.SECONDS
        )
        logger.info("mirrored Kafka offsets; group=%s", KAFKA_CONSUMER_GROUP)

    def onQueryTerminated(self, event):
        """Log query termination."""
        logger.info(f"stream terminated; query id={event.id}")
        self._admin.close()


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
    spark.streams.addListener(BatchLogger(spark.sparkContext._jvm))
    query = sink(parse(read_source(spark)))
    query.awaitTermination()


if __name__ == "__main__":
    main()
