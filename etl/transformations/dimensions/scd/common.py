"""
Shared helpers for SCD2 dimension loaders.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, concat_ws, current_timestamp, lit, sha2

DEFAULT_VALID_TO = "2099-12-31 23:59:59"


def build_new_version(
    df: DataFrame,
    load_version: int,
    generated_columns: list[str] | None = None,
) -> DataFrame:
    """
    Create active SCD2 versions.

    Warehouse-generated columns are removed because ClickHouse
    generates them during insert.
    """

    result = df.drop("_hash")

    if generated_columns:
        result = result.drop(*generated_columns)

    return (
        result.withColumn(
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
    df: DataFrame,
    load_version: int,
    generated_columns: list[str] | None = None,
) -> DataFrame:
    """
    Close existing active SCD2 versions.

    Warehouse-generated columns are removed because they are
    recreated by ClickHouse for new versions.
    """

    result = df.drop("_hash")

    if generated_columns:
        result = result.drop(*generated_columns)

    return (
        result.withColumn(
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


def add_hash(
    df: DataFrame,
    columns: list[str],
) -> DataFrame:
    """
    Add a hash column used for SCD2 change detection.

    The hash represents the current state of the dimension business
    attributes. If the hash changes compared to the active warehouse
    version, a new SCD2 version is created.

    Example:

        source:
            name = Farm A
            city = Belgrade

        current:
            name = Farm A
            city = Novi Sad

        hashes differ -> create new SCD2 version
    """

    return df.withColumn(
        "_hash",
        sha2(
            concat_ws(
                "||",
                *[col(column).cast("string") for column in columns],
            ),
            256,
        ),
    )
