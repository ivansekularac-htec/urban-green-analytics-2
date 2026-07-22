"""
Load fact_harvests incrementally into ClickHouse.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import col, from_unixtime, hour, minute
from transformations.common import (
    create_spark,
    read_batches_since,
    read_clickhouse,
    write_clickhouse,
)
from transformations.state import (
    get_watermark,
    set_watermark,
)

WATERMARK_PATH = "s3a://staging/_checkpoints/spark/fact_harvests/watermark.json"

SOURCE_PATH = "s3a://staging/raw/postgres/harvests/"


def transform_source(
    harvests_df: DataFrame,
) -> DataFrame:
    """
    Normalize raw harvest records for warehouse loading.
    """

    return harvests_df.select(
        col("id").alias("harvest_id"),
        col("farm_id"),
        col("crop_id"),
        col("quality_grade_id"),
        from_unixtime(col("created_at")).cast("timestamp").alias("harvested_at"),
        col("harvest_date"),
        col("weight_kg"),
    )


def add_farm_key(
    harvests_df: DataFrame,
    dim_farm_df: DataFrame,
) -> DataFrame:
    """
    Add farm_key by resolving the SCD2 farm version active
    when the harvest occurred.

    A farm_id can have multiple versions in dim_farm,
    therefore the join must include the harvested_at range.
    """

    return (
        harvests_df.alias("h")
        .join(
            dim_farm_df.alias("f"),
            (
                (col("h.farm_id") == col("f.farm_id"))
                & (col("h.harvested_at") >= col("f.valid_from"))
                & (col("h.harvested_at") < col("f.valid_to"))
            ),
            "left",
        )
        .select(
            col("h.*"),
            col("f.farm_key"),
        )
    )


def add_date_key(
    harvests_df: DataFrame,
    dim_date_df: DataFrame,
) -> DataFrame:
    """
    Add date_key from dim_date.
    """

    return (
        harvests_df.alias("h")
        .join(
            dim_date_df.alias("d"),
            col("h.harvest_date") == col("d.full_date"),
            "left",
        )
        .select(
            col("h.*"),
            col("d.date_key"),
        )
    )


def add_time_key(
    harvests_df: DataFrame,
) -> DataFrame:
    """
    Add minute-grain time_key.
    """

    return harvests_df.withColumn(
        "time_key",
        hour(col("harvested_at")) * 100 + minute(col("harvested_at")),
    )


def build_fact_harvests(
    harvests_df: DataFrame,
) -> DataFrame:
    """
    Build the final fact_harvests dataframe.
    """

    return harvests_df.select(
        col("harvest_id"),
        col("farm_key"),
        col("farm_id"),
        col("crop_id"),
        col("quality_grade_id"),
        col("date_key"),
        col("time_key"),
        col("harvested_at"),
        col("harvest_date"),
        col("weight_kg"),
    )


def transform_fact_harvests(
    harvests_df: DataFrame,
    dim_date_df: DataFrame,
    dim_farm_df: DataFrame,
) -> DataFrame:

    harvests_df = transform_source(harvests_df)

    harvests_df = add_date_key(
        harvests_df,
        dim_date_df,
    )

    harvests_df = add_time_key(
        harvests_df,
    )

    harvests_df = add_farm_key(
        harvests_df,
        dim_farm_df,
    )

    return build_fact_harvests(
        harvests_df,
    )


def main():

    spark = create_spark(
        "fact_harvests",
    )

    try:
        last_batch = get_watermark(
            spark,
            WATERMARK_PATH,
        )

        harvests_df, newest_batch = read_batches_since(
            spark,
            SOURCE_PATH,
            last_batch,
        )

        if harvests_df is None:
            print("No new harvest batches.")
            return

        dim_date_df = read_clickhouse(
            spark,
            "dim_date",
        )

        # Read all farm versions because this is an SCD2 dimension.
        # We need the historical version that was active at harvest time.
        dim_farm_df = read_clickhouse(
            spark,
            "dim_farm",
        )

        fact_df = transform_fact_harvests(
            harvests_df,
            dim_date_df,
            dim_farm_df,
        )

        # Fail fast instead of inserting orphaned facts.
        if fact_df.filter(col("farm_key").isNull()).limit(1).count():
            raise RuntimeError("One or more farm keys could not be resolved.")

        if fact_df.filter(col("date_key").isNull()).limit(1).count():
            raise RuntimeError("One or more date keys could not be resolved.")

        write_clickhouse(
            fact_df,
            "fact_harvests",
        )

        # Update watermark only after successful ClickHouse write.
        # If the job fails before this point, the same batches will retry.
        if newest_batch is not None:
            set_watermark(
                spark,
                WATERMARK_PATH,
                newest_batch,
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
