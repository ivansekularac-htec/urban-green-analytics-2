"""Load the latest user attributes into dim_user."""

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

SOURCE_TABLE = "users"
TARGET_TABLE = "dim_user"


def transform_users(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy("id").orderBy(F.col("updated_at").desc())

    return (
        dataframe.withColumn("_row_number", F.row_number().over(window))
        .filter(F.col("_row_number") == 1)
        .select(
            F.col("id").cast("long").alias("user_id"),
            F.lower(F.trim("email")).alias("email"),
            F.coalesce(
                F.trim("full_name"),
                F.lit(""),
            ).alias("full_name"),
            F.when(F.col("is_active"), 1).otherwise(0).cast("byte").alias("is_active"),
            F.to_timestamp(F.from_unixtime(F.col("created_at").cast("long"))).alias(
                "created_at"
            ),
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

        result = transform_users(source)

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
