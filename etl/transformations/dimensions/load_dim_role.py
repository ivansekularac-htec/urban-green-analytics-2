import logging

from common.clickhouse import write_clickhouse_table
from common.config import WarehouseSettings
from common.minio import latest_rows, read_full_table
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_dim_role"
TARGET_TABLE = "dim_role"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        roles_path = f"{settings.postgres_raw_root}/roles/"

        # Read all source batches and keep the latest row for each role.
        roles = latest_rows(
            read_full_table(
                spark,
                roles_path,
            )
        )

        # Transform the source data to match the ClickHouse schema.
        output = roles.select(
            F.col("id").cast("long").alias("role_id"),
            F.trim(F.col("name")).alias("name"),
            F.coalesce(F.trim(F.col("description")), F.lit("")).alias("description"),
            F.current_timestamp().alias("_loaded_at"),
        )

        # Append the current SCD Type 1 snapshot to ClickHouse.
        write_clickhouse_table(
            output,
            settings,
            TARGET_TABLE,
        )

        LOGGER.info(f"{TARGET_TABLE} loaded successfully.")

    except Exception:
        LOGGER.exception(f"{JOB_NAME} failed.")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
