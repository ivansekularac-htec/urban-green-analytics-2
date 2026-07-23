"""Load dim_sensor_type from the raw Postgres sensor_types extract.

Type 2 dimension. optimal_min and optimal_max decide whether a reading counts
as an anomaly, so their history has to be kept: a reading from last month must
be judged against the thresholds that applied last month, not against the
current ones.
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pyspark.sql import functions as F

from common import scd2
from common.spark import build_spark, read_raw_postgres
from common.transform import epoch_to_ts, latest_per_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SOURCE_TABLE = "sensor_types"
TARGET_TABLE = "dim_sensor_type"
NATURAL_KEY = "sensor_type_id"
SURROGATE = "sensor_type_key"

TRACKED_COLUMNS = ["name", "unit", "description", "optimal_min", "optimal_max"]


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        raw = read_raw_postgres(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        incoming = latest_per_key(raw, "id").select(
            F.col("id").cast("long").alias(NATURAL_KEY),
            F.col("name").cast("string").alias("name"),
            F.col("unit").cast("string").alias("unit"),
            F.coalesce(F.col("description"), F.lit("")).cast("string").alias("description"),
            F.coalesce(F.col("optimal_min"), F.lit(0)).cast("double").alias("optimal_min"),
            F.coalesce(F.col("optimal_max"), F.lit(0)).cast("double").alias("optimal_max"),
            epoch_to_ts("updated_at").alias("valid_from"),
        )

        scd2.apply_scd2(incoming, TARGET_TABLE, NATURAL_KEY, TRACKED_COLUMNS, SURROGATE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
