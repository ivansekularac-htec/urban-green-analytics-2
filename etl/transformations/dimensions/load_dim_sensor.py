"""Load dim_sensor from the raw Postgres sensors extract.

Type 2 dimension. A sensor is replaced, moved or taken out of service over
time, and a reading has to be attributed to the sensor as it was configured
when the reading arrived.

farm_key and sensor_type_key carry the natural Postgres ids, not SCD2
surrogates. A sensor version spans an interval rather than a single instant,
so it cannot point at one specific farm version: picking one would either go
stale the moment the farm changes, or force every sensor on that farm into a
new version and fabricate a sensor change that never happened. Queries select
the right farm version with a valid_from / valid_to condition instead. Facts
are different - an event has one fixed instant, so there the surrogate of the
version valid at that instant is resolved once and frozen.
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

SOURCE_TABLE = "sensors"
TARGET_TABLE = "dim_sensor"
NATURAL_KEY = "sensor_id"
SURROGATE = "sensor_key"

TRACKED_COLUMNS = [
    "farm_key",
    "sensor_type_key",
    "serial_number",
    "status",
    "installed_at",
]


def main():
    spark = build_spark(f"load_{TARGET_TABLE}")
    try:
        raw = read_raw_postgres(spark, SOURCE_TABLE)
        if raw is None:
            logger.warning(f"nothing to load into {TARGET_TABLE}")
            return

        incoming = latest_per_key(raw, "id").select(
            F.col("id").cast("long").alias(NATURAL_KEY),
            F.col("farm_id").cast("long").alias("farm_key"),
            F.col("sensor_type_id").cast("long").alias("sensor_type_key"),
            F.col("serial_number").cast("string").alias("serial_number"),
            F.col("status").cast("string").alias("status"),
            epoch_to_ts("installed_at").alias("installed_at"),
            epoch_to_ts("updated_at").alias("valid_from"),
        )

        scd2.apply_scd2(incoming, TARGET_TABLE, NATURAL_KEY, TRACKED_COLUMNS, SURROGATE)
    finally:
        spark.stop()


if __name__ == "__main__":
    main()
