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


def build_spark():
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
    return (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
        .option("subscribe", KAFKA_TOPIC)
        .option("startingOffsets", STARTING_OFFSETS)
        .option("failOnDataLoss", "false")
        .load()
    )


def parse(raw):
    decoded = raw.select(
        from_json(col("value").cast("string"), SENSOR_SCHEMA).alias("payload")
    ).select("payload.*")
    valid = decoded.filter(col("farm_sensor_id").isNotNull())
    return valid.withColumn("event_date", to_date(from_unixtime(col("timestamp"))))


def sink(events):
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
    spark = build_spark()
    spark.sparkContext.setLogLevel("WARN")
    query = sink(parse(read_source(spark)))
    query.awaitTermination()


if __name__ == "__main__":
    main()
