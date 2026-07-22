"""Load the latest quality grade attributes into dim_quality_grade."""

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

SOURCE_TABLE = "quality_grades"
TARGET_TABLE = "dim_quality_grade"


def transform_quality_grades(
    dataframe: DataFrame,
) -> DataFrame:
    window = Window.partitionBy("id").orderBy(F.col("updated_at").desc())

    code = F.upper(F.trim("code"))

    return (
        dataframe.withColumn("_row_number", F.row_number().over(window))
        .filter(F.col("_row_number") == 1)
        .select(
            F.col("id").cast("long").alias("quality_grade_id"),
            code.alias("code"),
            F.trim("name").alias("name"),
            F.coalesce(
                F.col("description"),
                F.lit(""),
            ).alias("description"),
            F.when(code == "A", 1).otherwise(0).cast("byte").alias("is_premium"),
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

        result = transform_quality_grades(source)

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
