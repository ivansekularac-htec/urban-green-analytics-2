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
        #
        # 1. Read current source snapshot
        #
        sensor_type_df = read_current_snapshot(
            spark,
            MINIO_STAGING_BUCKET,
            "sensor_types",
        )

        #
        # 2. Transform source shape
        #
        dim_sensor_type_source_df = transform_dim_sensor_type(
            sensor_type_df,
        )

        #
        # 3. Read current active SCD2 rows
        #
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

        #
        # 4. Hash attributes for change detection
        #
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

        #
        # 5. Find new and changed rows
        #
        new_sensor_types_df, changed_sensor_types_df = split_changes(
            source_hashed_df,
            current_hashed_df,
            "sensor_type_id",
        )

        #
        # 6. Find existing versions that need closing
        #
        expired_sensor_types_df = current_dim_sensor_type_df.join(
            changed_sensor_types_df.select(
                "sensor_type_id",
            ),
            "sensor_type_id",
            "inner",
        )

        #
        # 7. Create SCD2 versions
        #
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
                    changed_sensor_types_df,
                    load_version,
                )
            )
        )

        #
        # 8. Write to ClickHouse
        #
        write_clickhouse(
            rows_to_write,
            "dim_sensor_type",
        )

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
