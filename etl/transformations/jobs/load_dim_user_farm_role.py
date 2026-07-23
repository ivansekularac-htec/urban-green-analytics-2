"""
Executes the SCD2 loading of the dim_user_farm_role dimension.

The job performs the following steps:

1. Creates a SparkSession.
2. Reads the latest user-role snapshot from raw parquet sources
   stored in MinIO.
3. Reads the existing dimension state from ClickHouse.
4. Applies SCD2 comparison logic to detect new and changed records.
5. Writes generated dimension changes into ClickHouse.

The loader preserves historical versions of user-role assignments
and only appends records that represent changes in the source data.
"""

from common.clickhouse import read_clickhouse, write_to_clickhouse
from common.scd2 import apply_scd2
from common.spark import get_spark_session
from dimensions.dim_user_farm_role import create_dim_user_farm_role


def main():
    """
    Runs the dim_user_farm_role SCD2 ETL pipeline.

    The function creates a Spark session, generates the latest
    user-role snapshot, compares it with the existing ClickHouse
    dimension state, writes detected changes, and stops the Spark job.

    Returns
    -------
    None
    """

    spark = get_spark_session(
        "load-dim-user-farm-role",
    )

    try:
        snapshot = create_dim_user_farm_role(spark)

        existing = read_clickhouse(
            spark,
            "dim_user_farm_role",
        )

        changes = apply_scd2(
            snapshot_df=snapshot,
            current_df=existing,
            business_key="user_role_id",
            tracked_columns=[
                "user_id",
                "role_id",
                "farm_key",
                "farm_id",
                "user_full_name",
                "role_name",
                "farm_name",
            ],
        )

        if not changes.rdd.isEmpty():
            write_to_clickhouse(
                changes,
                "dim_user_farm_role",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
