import os
from dataclasses import dataclass

INITIAL_VALID_FROM = "2020-01-01 00:00:00"
MAX_VALID_TO = "2099-12-31 23:59:59"


@dataclass(frozen=True)
class WarehouseSettings:
    """Configuration shared by warehouse Spark jobs."""

    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket: str

    clickhouse_host: str
    clickhouse_http_port: int
    clickhouse_database: str
    clickhouse_user: str
    clickhouse_password: str

    jdbc_batch_size: int
    jdbc_write_partitions: int

    @classmethod
    def from_env(cls) -> "WarehouseSettings":
        return cls(
            minio_endpoint=os.getenv(
                "MINIO_ENDPOINT",
                "http://urbangreen-minio:9000",
            ),
            minio_access_key=os.getenv(
                "MINIO_ROOT_USER",
                "minioadmin",
            ),
            minio_secret_key=os.getenv(
                "MINIO_ROOT_PASSWORD",
                "",
            ),
            minio_bucket=os.getenv(
                "MINIO_STAGING_BUCKET",
                "staging",
            ),
            clickhouse_host=os.getenv(
                "CLICKHOUSE_HOST",
                "urbangreen-clickhouse",
            ),
            clickhouse_http_port=int(os.getenv("CLICKHOUSE_HTTP_PORT", "8123")),
            clickhouse_database=os.getenv(
                "CLICKHOUSE_DB",
                "urbangreen_dw",
            ),
            clickhouse_user=os.getenv(
                "CLICKHOUSE_USER",
                "urbangreen",
            ),
            clickhouse_password=os.getenv(
                "CLICKHOUSE_PASSWORD",
                "",
            ),
            jdbc_batch_size=int(
                os.getenv(
                    "CLICKHOUSE_JDBC_BATCH_SIZE",
                    "10000",
                )
            ),
            jdbc_write_partitions=int(
                os.getenv(
                    "CLICKHOUSE_JDBC_WRITE_PARTITIONS",
                    "2",
                )
            ),
        )

    @property
    def clickhouse_jdbc_url(self) -> str:
        return (
            f"jdbc:clickhouse://{self.clickhouse_host}:"
            f"{self.clickhouse_http_port}/"
            f"{self.clickhouse_database}"
        )

    @property
    def postgres_raw_root(self) -> str:
        return f"s3a://{self.minio_bucket}/raw/postgres"

    @property
    def kafka_raw_root(self) -> str:
        return f"s3a://{self.minio_bucket}/raw/kafka"
