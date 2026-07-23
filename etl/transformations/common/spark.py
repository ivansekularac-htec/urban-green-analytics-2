from pyspark.sql import SparkSession

from common.config import (
    MINIO_ACCESS_KEY,
    MINIO_ENDPOINT,
    MINIO_SECRET_KEY,
    SPARK_MASTER,
)


def get_spark_session(app_name):
    """
    Creates and configures a SparkSession used by ETL jobs.

    The session is configured to run on the Spark cluster,
    access data stored in MinIO through the S3A connector,
    and communicate with external systems such as Kafka and ClickHouse.
    """

    spark = (
        SparkSession.builder
        # Application name visible in Spark UI
        .appName(app_name)
        # Connect to Spark standalone cluster
        .master(SPARK_MASTER)
        # External dependencies required by Spark jobs
        # spark-sql-kafka: Enables reading from and writing to Kafka topics.
        # hadoop-aws: Provides S3A support for accessing MinIO/S3 storage.
        # clickhouse-jdbc: Allows writing DataFrames to ClickHouse using JDBC.
        .config(
            "spark.jars.packages",
            ",".join(
                [
                    "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.2",
                    "org.apache.hadoop:hadoop-aws:3.4.1",
                    "com.clickhouse:clickhouse-jdbc:0.9.8",
                ]
            ),
        )
        # =====================
        # MinIO / S3A configuration
        # =====================
        # MinIO server address
        .config("spark.hadoop.fs.s3a.endpoint", MINIO_ENDPOINT)
        # Credentials used by Spark executors to access the MinIO bucket
        .config("spark.hadoop.fs.s3a.access.key", MINIO_ACCESS_KEY)
        .config("spark.hadoop.fs.s3a.secret.key", MINIO_SECRET_KEY)
        # Required for MinIO because it uses path-style access instead of AWS virtual-host style
        .config("spark.hadoop.fs.s3a.path.style.access", "true")
        # Disable SSL because local MinIO runs over HTTP
        .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
        .getOrCreate()
    )

    # Reduce Spark logs to warnings/errors to keep ETL output cleaner
    spark.sparkContext.setLogLevel("WARN")

    return spark
