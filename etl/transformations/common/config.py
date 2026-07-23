import os

# =====================
# MinIO / S3
# =====================

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://urbangreen-minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ROOT_USER", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_ROOT_PASSWORD")
MINIO_BUCKET = os.getenv("MINIO_STAGING_BUCKET", "staging")

RAW_POSTGRES_PATH = f"s3a://{MINIO_BUCKET}/raw/postgres"
RAW_KAFKA_PATH = f"s3a://{MINIO_BUCKET}/raw/kafka"


# =====================
# ClickHouse
# =====================

CLICKHOUSE_HOST = os.getenv("CLICKHOUSE_HOST", "urbangreen-clickhouse")
CLICKHOUSE_PORT = os.getenv("CLICKHOUSE_HTTP_PORT", "8123")
CLICKHOUSE_DATABASE = os.getenv("CLICKHOUSE_DATABASE", "urbangreen_dw")
CLICKHOUSE_USER = os.getenv("CLICKHOUSE_USER", "urbangreen")
CLICKHOUSE_PASSWORD = os.getenv("CLICKHOUSE_PASSWORD")

CLICKHOUSE_URL = (
    f"jdbc:clickhouse://{CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DATABASE}"
)

AGG_REFRESH_DAYS = 7

# =====================
# Spark
# =====================

SPARK_MASTER = os.getenv("SPARK_MASTER", "spark://urbangreen-spark-master:7077")
