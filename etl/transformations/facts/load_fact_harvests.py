import logging

from common.clickhouse import (
    read_clickhouse_query,
    write_clickhouse_table,
)
from common.config import WarehouseSettings
from common.load_state import read_cursor, save_cursor
from common.minio import (
    find_new_batches,
    latest_rows,
    read_batches,
)
from common.spark_session import create_spark_session
from pyspark.sql import functions as F

JOB_NAME = "load_fact_harvests"
TARGET_TABLE = "fact_harvests"
CURSOR_KEY = "harvest_date"

LOGGER = logging.getLogger(JOB_NAME)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    settings = WarehouseSettings.from_env()
    spark = create_spark_session(JOB_NAME, settings)

    try:
        cursor = read_cursor(spark, settings, JOB_NAME)

        harvests_path = f"{settings.postgres_raw_root}/harvests/"

        # Find all harvest batches that have not been processed yet.
        batch_paths, new_watermark = find_new_batches(
            spark,
            harvests_path,
            cursor.get(CURSOR_KEY, 0),
        )

        if not batch_paths:
            LOGGER.info("No new data for fact_harvests.")
            return

        # Read all logical farm versions for the historical key lookup.
        farm_versions = read_clickhouse_query(
            spark,
            settings,
            f"""
            SELECT
                farm_id,
                farm_key,
                valid_from,
                valid_to
            FROM {settings.clickhouse_database}.dim_farm FINAL
            """,
        )

        if farm_versions.isEmpty():
            LOGGER.warning(
                "Skipping fact_harvests load: dim_farm contains no rows. "
                "Load dim_farm first. Cursor was not advanced."
            )
            return

        # Read new batches and keep the latest row for each harvest.
        harvests = latest_rows(read_batches(spark, batch_paths)).select(
            F.col("id").cast("long").alias("harvest_id"),
            F.col("farm_id").cast("long").alias("farm_id"),
            F.col("crop_id").cast("long").alias("crop_id"),
            F.col("quality_grade_id").cast("long").alias("quality_grade_id"),
            F.col("weight_kg").cast("decimal(10,3)").alias("weight_kg"),
            F.from_unixtime(F.col("created_at"))
            .cast("timestamp")
            .alias("harvested_at"),
        )

        harvest = harvests.alias("harvest")
        farm = farm_versions.alias("farm")

        # Match each harvest to the farm version valid at harvest time.
        matched_harvests = harvest.join(
            farm,
            (F.col("harvest.farm_id") == F.col("farm.farm_id"))
            & (F.col("harvest.harvested_at") >= F.col("farm.valid_from"))
            & (F.col("harvest.harvested_at") < F.col("farm.valid_to")),
            how="left",
        )

        # Do not advance the cursor when a farm key cannot be resolved.
        if (
            matched_harvests.filter(F.col("farm.farm_key").isNull()).limit(1).count()
            > 0
        ):
            raise ValueError(
                "Some harvest rows could not be matched to a dim_farm version."
            )

        output = matched_harvests.select(
            F.pmod(
                F.xxhash64(
                    F.lit("harvest"),
                    F.col("harvest.harvest_id"),
                ),
                F.lit(9_223_372_036_854_775_807),
            )
            .cast("decimal(20,0)")
            .alias("harvest_key"),
            F.col("harvest.harvest_id").alias("harvest_id"),
            F.col("farm.farm_key").alias("farm_key"),
            F.col("harvest.farm_id").alias("farm_id"),
            F.col("harvest.crop_id").alias("crop_id"),
            F.col("harvest.quality_grade_id").alias("quality_grade_id"),
            F.date_format(F.col("harvest.harvested_at"), "yyyyMMdd")
            .cast("int")
            .alias("date_key"),
            F.date_format(F.col("harvest.harvested_at"), "HHmmss")
            .cast("int")
            .alias("time_key"),
            F.col("harvest.harvested_at").alias("harvested_at"),
            F.to_date(F.col("harvest.harvested_at")).alias("harvest_date"),
            F.col("harvest.weight_kg").alias("weight_kg"),
            F.current_timestamp().alias("_loaded_at"),
        )

        write_clickhouse_table(
            output,
            settings,
            TARGET_TABLE,
        )

        # Advance the cursor only after the fact write succeeds.
        save_cursor(
            spark,
            settings,
            JOB_NAME,
            {CURSOR_KEY: new_watermark},
        )

        LOGGER.info(f"{TARGET_TABLE} loaded successfully.")

    except Exception:
        LOGGER.exception(f"{JOB_NAME} failed.")
        raise

    finally:
        spark.stop()


if __name__ == "__main__":
    main()
