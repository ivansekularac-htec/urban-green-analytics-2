"""
Structured Streaming ingestion for sensor readings.

Consumes JSON events from Kafka, parses them using an explicit schema,
derives an event-date partition column from the payload timestamp, and
writes partitioned Parquet files to MinIO with checkpointing enabled.
"""

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
        StructField("farm_sensor_id", IntegerType(), True),
        StructField("farm_id", IntegerType(), True),
        StructField("sensor_type_id", IntegerType(), True),
        StructField("value", DoubleType(), True),
        StructField("timestamp", LongType(), True),
    ]
)


def get_config():
    """
    Load runtime configuration from environment variables.

    Returns:
        dict: Kafka, MinIO, and streaming configuration.
    """
    return {
        # Spark
        "spark_master_url": (
            f"spark://{os.getenv('SPARK_MASTER_HOST', 'urbangreen-spark-master')}:"
            f"{os.getenv('SPARK_MASTER_PORT', '7077')}"
        ),
        "spark_driver_host": os.getenv("SPARK_DRIVER_HOST", "urbangreen-spark-driver"),
        "spark_worker_cores": os.getenv("SPARK_WORKER_CORES", "1"),
        "spark_worker_memory": os.getenv("SPARK_WORKER_MEMORY", "1g"),
        # Kafka
        "kafka_bootstrap_servers": (
            f"{os.getenv('KAFKA_HOST', 'urbangreen-kafka')}:"
            f"{os.getenv('KAFKA_PORT_INTERNAL', '9092')}"
        ),
        "kafka_topic": os.getenv("KAFKA_TOPIC_SENSOR_READINGS", "sensor_readings"),
        "starting_offsets": os.getenv("KAFKA_STARTING_OFFSETS", "earliest"),
        # MinIO
        "minio_endpoint": (
            f"http://{os.getenv('MINIO_HOST', 'urbangreen-minio')}:"
            f"{os.getenv('MINIO_API_PORT', '9000')}"
        ),
        "minio_access_key": os.getenv("MINIO_ROOT_USER", "minioadmin"),
        "minio_secret_key": os.getenv("MINIO_ROOT_PASSWORD"),
        "staging_bucket": os.getenv("MINIO_STAGING_BUCKET", "staging"),
        # Streaming
        "trigger_interval": os.getenv("STREAM_TRIGGER_INTERVAL", "60 seconds"),
    }


def create_spark_session(config):
    """
    Create and configure the Spark session.

    Args:
        config (dict): Runtime configuration.

    Returns:
        SparkSession: Configured Spark session.
    """
    return (
        SparkSession.builder.master(config["spark_master_url"])
        .appName("sensor_readings_stream")
        # Driver networking
        .config("spark.driver.host", config["spark_driver_host"])
        .config("spark.driver.bindAddress", "0.0.0.0")
        # Local cluster resources
        .config("spark.executor.cores", config["spark_worker_cores"])
        .config("spark.executor.memory", config["spark_worker_memory"])
        # MinIO / S3A
        .config("spark.hadoop.fs.s3a.endpoint", config["minio_endpoint"])
        .config("spark.hadoop.fs.s3a.access.key", config["minio_access_key"])
        .config("spark.hadoop.fs.s3a.secret.key", config["minio_secret_key"])
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .config(
            "spark.hadoop.fs.s3a.aws.credentials.provider",
            "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
        )
        .config("spark.sql.session.timeZone", "UTC")
        .config("spark.sql.streaming.schemaInference", "false")
        .getOrCreate()
    )


def read_kafka_stream(spark, config):
    """
    Read sensor readings from Kafka as a streaming DataFrame.

    Args:
        spark (SparkSession): Active Spark session.
        config (dict): Runtime configuration.

    Returns:
        DataFrame: Kafka streaming DataFrame.
    """
    return (
        spark.readStream.format("kafka")
        .option(
            "kafka.bootstrap.servers",
            config["kafka_bootstrap_servers"],
        )
        .option(
            "subscribe",
            config["kafka_topic"],
        )
        .option(
            "startingOffsets",
            config["starting_offsets"],
        )
        .option(
            "failOnDataLoss",
            "false",
        )
        .load()
    )


def parse_sensor_readings(df):
    """
    Parse Kafka JSON payloads using the explicit sensor schema and derive
    the event_date partition column.

    Args:
        df (DataFrame): Kafka streaming DataFrame.

    Returns:
        DataFrame: Parsed sensor readings with an event_date column.
    """
    return (
        df.select(
            from_json(
                col("value").cast("string"),
                SENSOR_SCHEMA,
            ).alias("data")
        )
        .select("data.*")
        .withColumn(
            "event_date",
            to_date(from_unixtime(col("timestamp"))),
        )
    )


def write_stream(df, config):
    """
    Write sensor readings to MinIO as partitioned Parquet.

    Args:
        df (DataFrame): Parsed streaming DataFrame.
        config (dict): Runtime configuration.

    Returns:
        StreamingQuery: Running streaming query.
    """
    output_path = f"s3a://{config['staging_bucket']}/raw/kafka/{config['kafka_topic']}/"

    checkpoint_path = (
        f"s3a://{config['staging_bucket']}/_checkpoints/kafka/{config['kafka_topic']}/"
    )

    return (
        df.writeStream.format("parquet")
        .outputMode("append")
        .option(
            "path",
            output_path,
        )
        .option(
            "checkpointLocation",
            checkpoint_path,
        )
        .partitionBy(
            "event_date",
        )
        .trigger(
            processingTime=config["trigger_interval"],
        )
        .start()
    )


def main():
    """
    Create and start the sensor readings streaming pipeline.
    """
    config = get_config()

    spark = create_spark_session(config)
    spark.sparkContext.setLogLevel("WARN")

    kafka_df = read_kafka_stream(
        spark,
        config,
    )

    parsed_df = parse_sensor_readings(
        kafka_df,
    )

    query = write_stream(
        parsed_df,
        config,
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
