"""
Shared helpers for SCD2 dimension loaders.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import current_timestamp, lit

DEFAULT_VALID_TO = "2099-12-31 23:59:59"


def build_new_version(
    df: DataFrame,
    load_version: int,
) -> DataFrame:
    """
    Create a new active SCD2 version.

    Source rows already represent changed records because Airflow
    extracts only rows whose updated_at changed.
    """

    return (
        df.withColumn(
            "valid_from",
            current_timestamp(),
        )
        .withColumn(
            "valid_to",
            lit(DEFAULT_VALID_TO).cast("timestamp"),
        )
        .withColumn(
            "is_current",
            lit(1),
        )
        .withColumn(
            "_version",
            lit(load_version),
        )
    )


def build_expired_version(
    current_df: DataFrame,
    load_version: int,
    surrogate_key: str,
) -> DataFrame:
    """
    Expire the current SCD2 version.

    The surrogate key is dropped so ClickHouse generates a new key
    for the expired version.
    """

    return (
        current_df.drop(
            surrogate_key,
        )
        .withColumn(
            "valid_to",
            current_timestamp(),
        )
        .withColumn(
            "is_current",
            lit(0),
        )
        .withColumn(
            "_version",
            lit(load_version),
        )
    )
