"""
Load the dim_sensor_type warehouse dimension as an SCD2 table.
"""

import os
import time

from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from transformations.common import (
    create_spark,
    read_clickhouse,
    read_current_snapshot,
    write_clickhouse,
)

from etl.transformations.dimensions.scd.common import (
    add_hash,
    build_expired_version,
    build_new_version,
    split_changes,
)

MINIO_STAGING_BUCKET = os.environ.get(
    "MINIO_STAGING_BUCKET",
    "staging",
)


def transform_dim_sensor_type(
    sensor_type_df: DataFrame,
) -> DataFrame:
    """
    Build dim_sensor_type warehouse shape from source snapshot.
    """

    return sensor_type_df.select(
        sensor_type_df.id.alias("sensor_type_id"),
        sensor_type_df.name,
        sensor_type_df.unit,
        sensor_type_df.description,
        sensor_type_df.optimal_min,
        sensor_type_df.optimal_max,
    )


def main():
    """
    Load dim_sensor_type as an SCD2 dimension.
    """

    spark = create_spark(
        "load_dim_sensor_type",
    )

    try:
        # Read the current state of all source tables.
        #
        # MinIO contains incremental batches, so this reconstructs the
        # latest PostgreSQL state by combining all batches and keeping
        # the newest record per primary key.
        sensor_type_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "sensor_types",
        )

        # Build the complete current dimension state.
        dim_sensor_type_source_df = transform_dim_sensor_type(
            sensor_type_df,
        )

        # Read currently active SCD2 versions from ClickHouse.
        current_dim_sensor_type_df = read_clickhouse(
            spark,
            """
            (
                SELECT *
                FROM dim_sensor_type FINAL
            ) AS dim_sensor_type
            """,
        ).filter(
            col("is_current") == 1,
        )

        # Add hashes to compare business attributes.
        #
        # The hash represents the state of the dimension row.
        # If the hash changes, a new SCD2 version is created.
        source_hashed_df = add_hash(
            dim_sensor_type_source_df,
            [
                "name",
                "unit",
                "description",
                "optimal_min",
                "optimal_max",
            ],
        )

        current_hashed_df = add_hash(
            current_dim_sensor_type_df,
            [
                "name",
                "unit",
                "description",
                "optimal_min",
                "optimal_max",
            ],
        )

        # Detect new rows and changed rows.
        new_sensor_types_df, changed_sensor_types_df = split_changes(
            source_hashed_df,
            current_hashed_df,
            "sensor_type_id",
        )

        # Find currently active versions that need to expire.
        expired_sensor_types_df = current_dim_sensor_type_df.join(
            changed_sensor_types_df.select(
                "sensor_type_id",
            ),
            "sensor_type_id",
            "inner",
        )

        # Changed source rows become new active versions.
        new_sensor_types_version_df = changed_sensor_types_df

        # One version identifier for this warehouse load.
        load_version = int(
            time.time() * 1000,
        )

        rows_to_write = (
            build_new_version(
                new_sensor_types_df,
                load_version,
            )
            .unionByName(
                build_expired_version(
                    expired_sensor_types_df,
                    load_version,
                    "sensor_type_key",
                )
            )
            .unionByName(
                build_new_version(
                    new_sensor_types_version_df,
                    load_version,
                )
            )
        )

        #
        # 8. Write to ClickHouse
        if rows_to_write.count() > 0:
            write_clickhouse(
                rows_to_write,
                "dim_sensor_type",
            )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
