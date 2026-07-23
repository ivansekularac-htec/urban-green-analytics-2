"""
Load fact_harvests incrementally into ClickHouse.
"""

import logging

from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from transformations.common import (
    create_spark,
    epoch_to_timestamp,
    read_clickhouse,
    read_incremental_parquet,
    write_clickhouse,
)
from transformations.facts.common import add_date_key, add_farm_key, add_time_key
from transformations.state import get_watermark, set_watermark

logger = logging.getLogger(__name__)

WATERMARK_PATH = "s3a://staging/_checkpoints/spark/fact_harvests/watermark.json"

SOURCE_PATH = "s3a://staging/raw/postgres/harvests/"


def transform_source(
    harvests_df: DataFrame,
) -> DataFrame:
    """
    Normalize raw harvest records for warehouse loading.
    """

    return harvests_df.select(
        harvests_df.id.alias("harvest_id"),
        "farm_id",
        "crop_id",
        "quality_grade_id",
        epoch_to_timestamp(harvests_df.created_at).alias("harvested_at"),
        "harvest_date",
        "weight_kg",
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
        "harvest_date",
    )

    harvests_df = add_time_key(
        harvests_df,
        "harvested_at",
    )

    harvests_df = add_farm_key(
        harvests_df,
        dim_farm_df,
        "harvested_at",
    )

    return harvests_df


def main():

    spark = create_spark(
        "fact_harvests",
    )

    try:
        last_watermark = get_watermark(
            spark,
            WATERMARK_PATH,
        )

        harvests_df, newest_watermark = read_incremental_parquet(
            spark,
            SOURCE_PATH,
            last_watermark,
        )

        if harvests_df is None:
            logger.info("No new harvest batches.")
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
        if newest_watermark is not None:
            set_watermark(
                spark,
                WATERMARK_PATH,
                newest_watermark,
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
