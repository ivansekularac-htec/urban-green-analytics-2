"""Load the latest application roles into dim_role."""

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

SOURCE_TABLE = "roles"
TARGET_TABLE = "dim_role"


def transform_roles(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy("id").orderBy(F.col("updated_at").desc())

    return (
        dataframe.withColumn("_row_number", F.row_number().over(window))
        .filter(F.col("_row_number") == 1)
        .select(
            F.col("id").cast("long").alias("role_id"),
            F.trim("name").alias("name"),
            F.coalesce(
                F.col("description"),
                F.lit(""),
            ).alias("description"),
        )
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

        result = transform_roles(source)

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
