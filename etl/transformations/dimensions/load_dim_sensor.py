"""Rebuild the dim_sensor SCD2 history and dimension relationships."""

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from transformations.common.clickhouse import read_clickhouse_table
from transformations.common.config import load_settings
from transformations.common.lake_reader import read_postgres_table
from transformations.common.spark_session import build_spark_session
from transformations.common.staging import full_refresh_table

TARGET_TABLE = "dim_sensor"
OPEN_END = "2099-12-31 23:59:59"


def transform(
    sensors: DataFrame,
    farms: DataFrame,
    sensor_types: DataFrame,
) -> DataFrame:
    sensors = sensors.withColumn(
        "_version",
        F.coalesce("updated_at", "created_at").cast("long"),
    )

    version_window = Window.partitionBy("id").orderBy("_version")

    sensors = (
        sensors.withColumn(
            "_version_rank",
            F.row_number().over(version_window),
        )
        .withColumn(
            "valid_from",
            F.when(
                F.col("_version_rank") == 1,
                F.coalesce(
                    F.to_timestamp(
                        F.from_unixtime(F.col("installed_at").cast("long"))
                    ),
                    F.to_timestamp(
                        F.from_unixtime(F.col("created_at").cast("long"))
                    ),
                    F.lit("1970-01-01 00:00:00").cast("timestamp"),
                ),
            ).otherwise(
                F.to_timestamp(F.from_unixtime("_version")),
            ),
        )
        .withColumn(
            "installed_at",
            F.to_timestamp(F.from_unixtime("installed_at")),
        )
        .dropDuplicates(["id", "valid_from"])
        .alias("s")
    )

    farms = farms.alias("f")
    sensor_types = sensor_types.alias("st")

    result = sensors.join(
        farms,
        (F.col("s.farm_id") == F.col("f.farm_id"))
        & (F.col("s.valid_from") >= F.col("f.valid_from"))
        & (F.col("s.valid_from") < F.col("f.valid_to")),
        "left",
    ).join(
        sensor_types,
        (F.col("s.sensor_type_id") == F.col("st.sensor_type_id"))
        & (F.col("s.valid_from") >= F.col("st.valid_from"))
        & (F.col("s.valid_from") < F.col("st.valid_to")),
        "left",
    )

    window = Window.partitionBy("s.id").orderBy("s.valid_from")
    result = result.withColumn(
        "next_valid_from",
        F.lead("s.valid_from").over(window),
    )

    return result.select(
        F.col("s.id").cast("long").alias("sensor_id"),
        F.col("f.farm_key"),
        F.col("st.sensor_type_key"),
        F.col("s.serial_number"),
        F.col("s.status"),
        F.col("s.installed_at"),
        F.col("s.valid_from"),
        F.coalesce(
            "next_valid_from",
            F.lit(OPEN_END).cast("timestamp"),
        ).alias("valid_to"),
        F.col("next_valid_from").isNull().cast("byte").alias("is_current"),
        F.col("s._version").cast("long").alias("_version"),
    )


def main() -> None:
    settings = load_settings()
    spark = build_spark_session(TARGET_TABLE, settings)

    try:
        result = transform(
            read_postgres_table(spark, settings, "sensors"),
            read_clickhouse_table(spark, settings, "dim_farm"),
            read_clickhouse_table(spark, settings, "dim_sensor_type"),
        )

        full_refresh_table(result, settings, TARGET_TABLE)
        logging.info("Loaded %s", TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
