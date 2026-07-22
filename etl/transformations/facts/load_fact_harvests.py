"""Incrementally load harvest facts and advance the successful-run cursor."""

import logging
import sys
from pathlib import Path

from pyspark.sql import DataFrame, Window
from pyspark.sql import functions as F

ETL_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ETL_ROOT))


from transformations.common.clickhouse import (
    read_clickhouse_table,
    write_clickhouse_table,
)
from transformations.common.config import load_settings
from transformations.common.lake_reader import read_postgres_table
from transformations.common.load_state import (
    commit_cursor,
    read_cursor,
)
from transformations.common.spark_session import build_spark_session
from transformations.common.temporal_join import temporal_condition

JOB_NAME = "load_fact_harvests"
SOURCE_TABLE = "harvests"
TARGET_TABLE = "fact_harvests"

DEFAULT_CURSOR = 0


def latest_by_id(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy("id").orderBy(
        F.col("updated_at").desc(),
    )

    return (
        dataframe.withColumn(
            "_row_number",
            F.row_number().over(window),
        )
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )


def transform_harvests(
    harvests: DataFrame,
    farms: DataFrame,
) -> DataFrame:
    harvests = (
        latest_by_id(harvests)
        .withColumn(
            "harvested_at",
            F.to_timestamp(
                F.from_unixtime(
                    F.col("created_at").cast("long"),
                )
            ),
        )
        .alias("h")
    )

    farms = farms.select(
        "farm_key",
        "farm_id",
        "valid_from",
        "valid_to",
    ).alias("f")

    joined = harvests.join(
        farms,
        temporal_condition(
            F.col("h.farm_id"),
            F.col("f.farm_id"),
            F.col("h.harvested_at"),
            F.col("f.valid_from"),
            F.col("f.valid_to"),
        ),
        "left",
    )

    harvested_at = F.col("h.harvested_at")

    return joined.select(
        F.col("h.id").cast("long").alias("harvest_key"),
        F.col("h.id").cast("long").alias("harvest_id"),
        F.col("f.farm_key"),
        F.col("h.farm_id").cast("long").alias("farm_id"),
        F.col("h.crop_id").cast("long").alias("crop_id"),
        F.col("h.quality_grade_id").cast("long").alias("quality_grade_id"),
        F.date_format(
            harvested_at,
            "yyyyMMdd",
        )
        .cast("int")
        .alias("date_key"),
        (F.hour(harvested_at) * 100 + F.minute(harvested_at))
        .cast("int")
        .alias("time_key"),
        harvested_at.alias("harvested_at"),
        F.to_date(harvested_at).alias("harvest_date"),
        F.col("h.weight_kg").cast("decimal(10,3)").alias("weight_kg"),
    )


def validate_result(
    dataframe: DataFrame,
) -> None:
    missing_farms = (
        dataframe.filter(F.col("farm_key").isNull())
        .select(
            "harvest_id",
            "farm_id",
            "harvested_at",
        )
        .limit(10)
        .collect()
    )

    if missing_farms:
        raise ValueError(
            f"Some harvests do not match a dim_farm version: {missing_farms}"
        )


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    settings = load_settings()
    spark = build_spark_session(JOB_NAME, settings)

    try:
        saved_cursor = read_cursor(
            spark,
            settings,
            JOB_NAME,
        )

        cursor_updated_at = int(
            (saved_cursor or {}).get(
                "updated_at",
                DEFAULT_CURSOR,
            )
        )

        source = read_postgres_table(
            spark,
            settings,
            SOURCE_TABLE,
        )

        new_source = source.filter(F.col("updated_at") > cursor_updated_at).cache()

        if new_source.isEmpty():
            logging.info(
                "No new %s rows after cursor %s",
                SOURCE_TABLE,
                cursor_updated_at,
            )
            return

        next_cursor = int(
            new_source.agg(F.max("updated_at").alias("updated_at")).first()[
                "updated_at"
            ]
        )

        farms = read_clickhouse_table(
            spark,
            settings,
            "dim_farm",
        )

        result = transform_harvests(
            new_source,
            farms,
        ).cache()

        validate_result(result)

        write_clickhouse_table(
            result,
            settings,
            TARGET_TABLE,
        )

        commit_cursor(
            settings,
            JOB_NAME,
            {
                "updated_at": next_cursor,
            },
        )

        logging.info(
            "Loaded %s and advanced cursor %s -> %s",
            TARGET_TABLE,
            cursor_updated_at,
            next_cursor,
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
