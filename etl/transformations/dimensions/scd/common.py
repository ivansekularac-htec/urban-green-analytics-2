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
    valid_from=None,
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
            lit(valid_from).cast("timestamp") if valid_from else current_timestamp(),
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


def split_changes(
    source_df: DataFrame,
    current_df: DataFrame,
    business_key: str,
) -> tuple[DataFrame, DataFrame]:
    """
    Compare source snapshot with current SCD2 rows.

    Returns:
        new_rows_df:
            Records that do not exist in the dimension yet.

        changed_rows_df:
            Records that exist but have changed attributes.
    """

    comparison_df = source_df.alias("source").join(
        current_df.alias("current"),
        business_key,
        "left",
    )

    new_rows_df = comparison_df.filter(
        col(f"current.{business_key}").isNull(),
    ).select(
        "source.*",
    )

    changed_rows_df = comparison_df.filter(
        col(f"current.{business_key}").isNotNull()
        & (col("source._hash") != col("current._hash"))
    ).select(
        "source.*",
    )

    return (
        new_rows_df,
        changed_rows_df,
    )


def get_initial_valid_from(
    current_dim_df: DataFrame,
) -> str | None:
    """
    Return initial SCD2 valid_from date for the first load.

    On initial dimension load, historical compatibility is needed
    because fact records may exist before the warehouse dimension.
    For subsequent loads, new versions should use current_timestamp().
    """

    if current_dim_df.isEmpty():
        return "1970-01-01 00:00:00"

    return None
