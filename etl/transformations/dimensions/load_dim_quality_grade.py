"""Load dim_quality_grade from the raw Postgres quality_grades extract.

Type 1 dimension: one current row per grade. is_premium is derived here rather
than read from the source, which carries no such column - see
config.PREMIUM_QUALITY_CODES for the rule and why it keys on the code.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse, config
from common.spark import build_spark, read_raw_postgres
from common.transform import latest_per_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "quality_grades"
TARGET_TABLE = "dim_quality_grade"


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        raw = read_raw_postgres(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        current = latest_per_key(raw, "id")

        premium_codes = list(config.PREMIUM_QUALITY_CODES)

        target = current.select(
            F.col("id").cast("long").alias("quality_grade_id"),
            F.col("code").cast("string").alias("code"),
            F.col("name").cast("string").alias("name"),
            F.coalesce(F.col("description"), F.lit("")).cast("string").alias("description"),
            F.col("code").isin(premium_codes).cast("tinyint").alias("is_premium"),
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
