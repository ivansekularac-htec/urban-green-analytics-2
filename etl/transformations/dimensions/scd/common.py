"""
Shared helpers for SCD2 dimension loaders.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, concat_ws, current_timestamp, lit, sha2

DEFAULT_VALID_TO = "2099-12-31 23:59:59"


def add_hash(
    df: DataFrame,
    columns: list[str],
) -> DataFrame:
    """
    Add a hash column used to detect SCD2 changes.
    """

    return df.withColumn(
        "_hash",
        sha2(
            concat_ws(
                "||",
                *[col(column) for column in columns],
            ),
            256,
        ),
    )


def split_changes(
    source_df: DataFrame,
    current_df: DataFrame,
    key: str,
) -> tuple[DataFrame, DataFrame, DataFrame]:
    """
    Compare source and current dimension rows.

    Returns:
    - new rows
    - changed rows
    """

    comparison_df = source_df.alias("source").join(
        current_df.alias("current"),
        key,
        "left",
    )

    new_rows = comparison_df.filter(col(f"current.{key}").isNull())

    changed_rows = comparison_df.filter(
        (col(f"current.{key}").isNotNull())
        & (col("source._hash") != col("current._hash"))
    )

    return (
        new_rows,
        changed_rows,
    )


def build_new_version(
    df: DataFrame,
    load_version: int,
) -> DataFrame:
    """
    Create active SCD2 versions from source rows.
    """

    return (
        df.select("source.*")
        .drop("_hash")
        .withColumn("valid_from", current_timestamp())
        .withColumn("valid_to", lit(DEFAULT_VALID_TO).cast("timestamp"))
        .withColumn("is_current", lit(1))
        .withColumn("_version", lit(load_version))
    )


def build_expired_version(
    df: DataFrame,
    load_version: int,
    surrogate_key: str,
) -> DataFrame:
    """
    Close existing active SCD2 versions.

    Warehouse-generated surrogate keys are removed because each
    SCD2 version receives a new key when inserted.
    """

    return (
        df.select("current.*")
        .drop(
            "_hash",
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
