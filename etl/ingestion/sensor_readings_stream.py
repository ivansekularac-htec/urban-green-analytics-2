import os

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import DoubleType, IntegerType, LongType, StructField, StructType

os.environ["JAVA_HOME"] = r"C:\Program Files\Java\jdk-17"
os.environ["HADOOP_HOME"] = "C:\\hadoop"

MINIO_ROOT_USER = os.environ.get("MINIO_ROOT_USER")
MINIO_ROOT_PASSWORD = os.environ.get("MINIO_ROOT_PASSWORD")

SPARK_MINIO_ENDPOINT = os.environ.get(
    "SPARK_MINIO_ENDPOINT", "http://urbangreen-minio:9000"
)
SIMULATOR_KAFKA_BOOTSTRAP = os.environ.get(
    "SIMULATOR_KAFKA_BOOTSTRAP", "urbangreen-kafka:9092"
)

KAFKA_TOPIC_SENSOR_READINGS = os.environ.get(
    "KAFKA_TOPIC_SENSOR_READINGS", "sensor_readings"
)
SPARK_KAFKA_OFFSET = os.environ.get("SPARK_KAFKA_OFFSET", "earliest")

# Start spark session

spark = (
    SparkSession.builder.appName("Sensor Readings Stream")
    .config(
        "spark.jars.packages",
        "org.apache.spark:spark-sql-kafka-0-10_2.13:4.0.2,org.apache.hadoop:hadoop-aws:3.4.1",
    )
    .config("spark.hadoop.fs.s3a.endpoint", SPARK_MINIO_ENDPOINT)
    .config("spark.hadoop.fs.s3a.access.key", MINIO_ROOT_USER)
    .config("spark.hadoop.fs.s3a.secret.key", MINIO_ROOT_PASSWORD)
    .config("spark.hadoop.fs.s3a.path.style.access", "true")
    .config("spark.hadoop.fs.s3a.connection.ssl.enabled", "false")
    .config(
        "spark.hadoop.fs.s3a.aws.credentials.provider",
        "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider",
    )
    .config("spark.sql.streaming.schemaInference", "false")
    .getOrCreate()
)

SENSOR_SCHEMA = StructType(
    [
        StructField("farm_sensor_id", IntegerType(), True),
        StructField("farm_id", IntegerType(), True),
        StructField("sensor_type_id", IntegerType(), True),
        StructField("value", DoubleType(), True),
        StructField("timestamp", LongType(), True),
    ],
)

# Read Kafka stream

kafka_df = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", SIMULATOR_KAFKA_BOOTSTRAP)
    .option("subscribe", KAFKA_TOPIC_SENSOR_READINGS)
    .option("startingOffsets", SPARK_KAFKA_OFFSET)
    .option("failOnDataLoss", "false")
    .load()
)

# Parse JSON using explicit StructType

parsed_df = from_json(col("value").cast("string"), SENSOR_SCHEMA)
