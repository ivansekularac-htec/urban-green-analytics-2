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


def get_config():
    return {
        "minio_root_user": os.environ.get("MINIO_ROOT_USER", "minio"),
        "minio_root_password": os.environ.get("MINIO_ROOT_PASSWORD", "miniominio"),
        "minio_endpoint": os.environ.get(
            "SPARK_MINIO_ENDPOINT",
            "http://urbangreen-minio:9000",
        ),
        "kafka_topic": os.environ.get(
            "KAFKA_TOPIC_SENSOR_READINGS",
            "sensor_readings",
        ),
        "kafka_bootstrap": os.environ.get(
            "SIMULATOR_KAFKA_BOOTSTRAP",
            "urbangreen-kafka:9092",
        ),
        "kafka_offset": os.environ.get(
            "SPARK_KAFKA_OFFSET",
            "earliest",
        ),
        "bucket": os.environ.get(
            "MINIO_STAGING_BUCKET",
            "staging",
        ),
        "trigger_interval": os.environ.get(
            "STREAM_TRIGGER_INTERVAL",
            "60 seconds",
        ),
    }


def create_spark_session(config):
    return (
        SparkSession.builder.appName("Sensor Readings Stream")
        .config(
            "spark.hadoop.fs.s3a.endpoint",
            config["minio_endpoint"],
        )
        .config(
            "spark.hadoop.fs.s3a.access.key",
            config["minio_root_user"],
        )
        .config(
            "spark.hadoop.fs.s3a.secret.key",
            config["minio_root_password"],
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
            "spark.jars.packages",
            ",".join(
                [
                    "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.2",
                    "org.apache.hadoop:hadoop-aws:3.4.1",
                    "com.amazonaws:aws-java-sdk-bundle:1.12.782",
                ]
            ),
        )
        .getOrCreate()
    )


def sensor_schema():
    return StructType(
        [
            StructField("farm_sensor_id", IntegerType(), True),
            StructField("farm_id", IntegerType(), True),
            StructField("sensor_type_id", IntegerType(), True),
            StructField("value", DoubleType(), True),
            StructField("timestamp", LongType(), True),
        ]
    )


def read_kafka_stream(spark, config):
    return (
        spark.readStream.format("kafka")
        .option(
            "kafka.bootstrap.servers",
            config["kafka_bootstrap"],
        )
        .option(
            "subscribe",
            config["kafka_topic"],
        )
        .option(
            "startingOffsets",
            config["kafka_offset"],
        )
        .option(
            "failOnDataLoss",
            "false",
        )
        .load()
    )


def transform_sensor_readings(df):

    raw_df = df.select(col("value").cast("string").alias("value"))

    parsed_df = raw_df.withColumn(
        "data",
        from_json(
            col("value"),
            sensor_schema(),
        ),
    ).select("data.*")

    return parsed_df.withColumn(
        "event_date",
        to_date(from_unixtime(col("timestamp"))),
    )


def write_stream(df, config):

    return (
        df.writeStream.format("parquet")
        .outputMode("append")
        .partitionBy("event_date")
        .option(
            "path",
            f"s3a://{config['bucket']}/raw/kafka/{config['kafka_topic']}/",
        )
        .option(
            "checkpointLocation",
            f"s3a://{config['bucket']}/_checkpoints/kafka/{config['kafka_topic']}/",
        )
        .trigger(processingTime=config["trigger_interval"])
        .start()
    )


def main():

    config = get_config()

    spark = create_spark_session(config)

    kafka_df = read_kafka_stream(
        spark,
        config,
    )

    transformed_df = transform_sensor_readings(kafka_df)

    query = write_stream(
        transformed_df,
        config,
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
