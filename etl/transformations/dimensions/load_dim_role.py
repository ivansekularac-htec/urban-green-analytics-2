"""Load dim_role from the raw Postgres roles extract.

Type 1 dimension: one current row per role. The loader reads every extracted
slice, keeps the newest row per role_id, and appends. dim_role is a
ReplacingMergeTree ordered by role_id, so repeated runs over the same source
collapse to a single row per key instead of accumulating.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import clickhouse
from common.spark import build_spark, read_raw_postgres
from common.transform import latest_per_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "roles"
TARGET_TABLE = "dim_role"


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        raw = read_raw_postgres(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        current = latest_per_key(raw, "id")

        target = current.select(
            F.col("id").cast("long").alias("role_id"),
            F.col("name").cast("string").alias("name"),
            F.coalesce(F.col("description"), F.lit("")).cast("string").alias("description"),
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
