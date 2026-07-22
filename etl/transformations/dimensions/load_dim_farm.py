"""Rebuild the dim_farm SCD2 history from raw farm snapshots."""

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

TARGET_TABLE = "dim_farm"
OPEN_END = "2099-12-31 23:59:59"


def latest_lookup(
    dataframe: DataFrame,
    id_name: str,
    value_name: str,
) -> DataFrame:
    window = Window.partitionBy("id").orderBy(F.col("updated_at").desc())

    return (
        dataframe.withColumn("_row_number", F.row_number().over(window))
        .filter(F.col("_row_number") == 1)
        .select(
            F.col("id").alias(id_name),
            F.trim("name").alias(value_name),
        )
    )


def transform_farms(
    farms: DataFrame,
    infrastructure_types: DataFrame,
    growing_system_types: DataFrame,
) -> DataFrame:
    infrastructure_types = latest_lookup(
        infrastructure_types,
        "infrastructure_lookup_id",
        "infrastructure_type_name",
    )

    growing_system_types = latest_lookup(
        growing_system_types,
        "growing_system_lookup_id",
        "growing_system_type_name",
    )

    farms = farms.withColumn(
        "_source_version",
        F.coalesce(
            F.col("updated_at"),
            F.col("created_at"),
        ).cast("long"),
    )

    version_window = Window.partitionBy("id").orderBy("_source_version")

    farms = (
        farms.withColumn(
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
        .join(
            infrastructure_types,
            F.col("infrastructure_type_id") == F.col("infrastructure_lookup_id"),
            "left",
        )
        .join(
            growing_system_types,
            F.col("growing_system_type_id") == F.col("growing_system_lookup_id"),
            "left",
        )
    )

    window = Window.partitionBy("id").orderBy("valid_from")

    farms = farms.withColumn(
        "_next_valid_from",
        F.lead("valid_from").over(window),
    )

    return farms.select(
        F.col("id").cast("long").alias("farm_id"),
        F.trim("name").alias("name"),
        F.trim("city").alias("city"),
        F.col("size_m2").cast("decimal(10,3)").alias("size_m2"),
        F.col("growing_beds_count").cast("int").alias("growing_beds_count"),
        F.trim("status").alias("status"),
        F.col("infrastructure_type_id").cast("long").alias("infrastructure_type_id"),
        F.col("infrastructure_type_name"),
        F.col("growing_system_type_id").cast("long").alias("growing_system_type_id"),
        F.col("growing_system_type_name"),
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
        farms = read_postgres_table(
            spark,
            settings,
            "farms",
        )

        infrastructure_types = read_postgres_table(
            spark,
            settings,
            "farm_infrastructure_types",
        )

        growing_system_types = read_postgres_table(
            spark,
            settings,
            "growing_system_types",
        )

        result = transform_farms(
            farms,
            infrastructure_types,
            growing_system_types,
        )

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
