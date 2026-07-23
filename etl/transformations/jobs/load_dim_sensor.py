"""
Executes the SCD2 loading of the sensor dimension.

The job performs the following steps:

1. Creates a SparkSession.
2. Reads the latest sensor snapshot from raw parquet sources
   stored in MinIO.
3. Reads the existing dimension state from ClickHouse.
4. Applies SCD2 comparison logic to detect new and changed records.
5. Writes generated dimension changes into ClickHouse.

The loader preserves historical versions of sensors
and only appends records that represent changes in the source data.
"""

from common.clickhouse import read_clickhouse, write_to_clickhouse
from common.scd2 import apply_scd2
from common.spark import get_spark_session
from dimensions.dim_sensor import create_dim_sensor


def main():
    """
    Runs the dim_sensor SCD2 ETL pipeline.

    The function creates a Spark session, generates the latest
    sensor snapshot, compares it with the existing ClickHouse
    dimension, writes detected changes, and stops the Spark job.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-dim-sensor",
    )

    try:
        snapshot = create_dim_sensor(
            spark,
        )

        existing = read_clickhouse(
            spark,
            "dim_sensor",
        )

        changes = apply_scd2(
            snapshot_df=snapshot,
            current_df=existing,
            business_key="sensor_id",
            tracked_columns=[
                "farm_key",
                "sensor_type_key",
                "serial_number",
                "status",
                "installed_at",
            ],
        )

        if not changes.rdd.isEmpty():
            write_to_clickhouse(
                changes,
                "dim_sensor",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
