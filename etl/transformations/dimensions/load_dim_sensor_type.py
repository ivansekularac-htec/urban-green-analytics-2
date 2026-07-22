"""Rebuild the dim_sensor_type SCD2 history from raw snapshots."""

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

ETL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETL_ROOT))


from transformations.common.config import load_settings
from transformations.common.lake_reader import read_postgres_table
from transformations.common.spark_session import build_spark_session
from transformations.common.staging import full_refresh_table

SOURCE_TABLE = "sensor_types"
TARGET_TABLE = "dim_sensor_type"

OPEN_END = "2099-12-31 23:59:59"


def transform_sensor_types(
    dataframe: DataFrame,
) -> DataFrame:
    versions = dataframe.withColumn(
        "_source_version",
        F.col("updated_at").cast("long"),
    )

    version_window = Window.partitionBy("id").orderBy("_source_version")

    versions = (
        versions.withColumn(
            "_version_rank",
            F.row_number().over(version_window),
        )
        .withColumn(
            "valid_from",
            F.when(
                F.col("_version_rank") == 1,
                F.lit("1970-01-01 00:00:00").cast("timestamp"),
            ).otherwise(
                F.to_timestamp(F.from_unixtime("_source_version")),
            ),
        )
        .dropDuplicates(["id", "valid_from"])
    )

    window = Window.partitionBy("id").orderBy("valid_from")

    versions = versions.withColumn(
        "_next_valid_from",
        F.lead("valid_from").over(window),
    )

    return versions.select(
        F.col("id").cast("long").alias("sensor_type_id"),
        F.trim("name").alias("name"),
        F.trim("unit").alias("unit"),
        F.coalesce(
            F.col("description"),
            F.lit(""),
        ).alias("description"),
        F.col("optimal_min").cast("double").alias("optimal_min"),
        F.col("optimal_max").cast("double").alias("optimal_max"),
        F.col("valid_from"),
        F.coalesce(
            F.col("_next_valid_from"),
            F.lit(OPEN_END).cast("timestamp"),
        ).alias("valid_to"),
        F.when(
            F.col("_next_valid_from").isNull(),
            1,
        )
        .otherwise(0)
        .cast("byte")
        .alias("is_current"),
        F.col("_source_version").alias("_version"),
    )


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    spark = build_spark_session(TARGET_TABLE, settings)

    try:
        source = read_postgres_table(
            spark,
            settings,
            SOURCE_TABLE,
        )

        result = transform_sensor_types(source)

        full_refresh_table(
            result,
            settings,
            TARGET_TABLE,
        )

        logging.info("Loaded %s", TARGET_TABLE)

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
