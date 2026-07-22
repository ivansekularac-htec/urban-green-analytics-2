"""Provide JDBC and HTTP helpers for ClickHouse access."""

import base64
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from pyspark.sql import DataFrame, SparkSession

from .config import Settings


def table_name(
    settings: Settings,
    name: str,
) -> str:
    return f"{settings.clickhouse_database}.{name}"


def jdbc_options(
    settings: Settings,
) -> dict[str, str]:
    return {
        "url": settings.clickhouse_jdbc_url,
        "user": settings.clickhouse_user,
        "password": settings.clickhouse_password,
        "driver": "com.clickhouse.jdbc.ClickHouseDriver",
    }


def read_clickhouse_table(
    spark: SparkSession,
    settings: Settings,
    name: str,
) -> DataFrame:
    return (
        spark.read.format("jdbc")
        .options(**jdbc_options(settings))
        .option("dbtable", table_name(settings, name))
        .load()
    )


def write_clickhouse_table(
    dataframe: DataFrame,
    settings: Settings,
    name: str,
) -> None:
    (
        dataframe.write.format("jdbc")
        .options(**jdbc_options(settings))
        .option("dbtable", table_name(settings, name))
        .mode("append")
        .save()
    )


def execute_clickhouse_sql(
    settings: Settings,
    sql: str,
) -> None:
    query = urlencode({"database": settings.clickhouse_database})

    credentials = f"{settings.clickhouse_user}:{settings.clickhouse_password}"

    authorization = base64.b64encode(credentials.encode()).decode()

    request = Request(
        url=f"{settings.clickhouse_http_url}?{query}",
        data=sql.encode(),
        method="POST",
        headers={
            "Authorization": f"Basic {authorization}",
        },
    )

    with urlopen(request, timeout=30):
        pass
