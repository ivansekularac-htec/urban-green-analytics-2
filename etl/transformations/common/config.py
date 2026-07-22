"""Load environment-backed settings for warehouse transformation jobs."""

import os
from dataclasses import dataclass


def required_env(name: str) -> str:
    value = os.getenv(name)

    if not value:
        raise ValueError(f"Missing environment variable: {name}")

    return value


@dataclass(frozen=True)
class Settings:
    minio_endpoint: str
    minio_user: str
    minio_password: str
    minio_bucket: str
    postgres_raw_prefix: str
    kafka_raw_prefix: str

    clickhouse_host: str
    clickhouse_port: int
    clickhouse_database: str
    clickhouse_user: str
    clickhouse_password: str

    @property
    def clickhouse_jdbc_url(self) -> str:
        return (
            f"jdbc:clickhouse://{self.clickhouse_host}:"
            f"{self.clickhouse_port}/{self.clickhouse_database}"
        )

    @property
    def clickhouse_http_url(self) -> str:
        return f"http://{self.clickhouse_host}:{self.clickhouse_port}/"


def load_settings() -> Settings:
    return Settings(
        minio_endpoint=os.getenv(
            "MINIO_ENDPOINT",
            "http://urbangreen-minio:9000",
        ),
        minio_user=required_env("MINIO_ROOT_USER"),
        minio_password=required_env("MINIO_ROOT_PASSWORD"),
        minio_bucket=required_env("MINIO_STAGING_BUCKET"),
        postgres_raw_prefix=os.getenv(
            "POSTGRES_RAW_PREFIX",
            "raw/postgres",
        ),
        kafka_raw_prefix=os.getenv(
            "KAFKA_RAW_PREFIX",
            "raw/kafka",
        ),
        clickhouse_host=os.getenv(
            "CLICKHOUSE_HOST",
            "urbangreen-clickhouse",
        ),
        clickhouse_port=int(
            os.getenv(
                "CLICKHOUSE_PORT",
                os.getenv("CLICKHOUSE_HTTP_PORT", "8123"),
            )
        ),
        clickhouse_database=os.getenv(
            "CLICKHOUSE_DB",
            "urbangreen_dw",
        ),
        clickhouse_user=os.getenv(
            "CLICKHOUSE_USER",
            "default",
        ),
        clickhouse_password=os.getenv(
            "CLICKHOUSE_PASSWORD",
            "",
        ),
    )
