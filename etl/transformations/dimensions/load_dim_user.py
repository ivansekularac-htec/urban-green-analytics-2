"""Load dim_user from the raw Postgres users extract.

Type 1 dimension: one current row per user. Columns are selected explicitly so
password_hash cannot reach the warehouse - the warehouse is read by reporting
tools and holds no credentials.
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

SOURCE_TABLE = "users"
TARGET_TABLE = "dim_user"


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        raw = read_raw_postgres(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        current = latest_per_key(raw, "id")

        target = current.select(
            F.col("id").cast("long").alias("user_id"),
            F.col("email").cast("string").alias("email"),
            F.col("full_name").cast("string").alias("full_name"),
            F.col("is_active").cast("tinyint").alias("is_active"),
            F.col("created_at").cast("timestamp").alias("created_at"),
        )

        clickhouse.write_table(target, TARGET_TABLE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
