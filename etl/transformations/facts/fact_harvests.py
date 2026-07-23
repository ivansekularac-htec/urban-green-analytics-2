"""
Creates fact_harvests fact table from raw PostgreSQL parquet data.

The transformation reads harvest records from raw parquet sources,
converts source timestamps into warehouse date and time attributes,
and enriches the data with surrogate keys from warehouse dimensions.

The extraction is incremental and uses the source updated_at timestamp
as a cursor. Only records newer than the stored cursor are processed.
"""

from common.clickhouse import read_clickhouse
from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql.functions import (
    col,
    concat_ws,
    from_unixtime,
    hour,
    minute,
    to_date,
    xxhash64,
)
from pyspark.sql.functions import (
    max as spark_max,
)

HARVESTS_PATH = f"{RAW_POSTGRES_PATH}/harvests/"


def create_fact_harvest(
    spark,
    cursor=None,
):
    """
    Creates incremental fact_harvests dataframe.

    The function:

    - reads latest harvest records from raw parquet files
    - applies incremental filtering using updated_at cursor
    - generates a warehouse surrogate key
    - converts source timestamps into date and time attributes
    - enriches records with farm, crop, quality, date, and time dimensions

    Parameters
    ----------
    spark : SparkSession
        Active Spark session.

    cursor : dict, optional
        Previously stored incremental loading cursor.

    Returns
    -------
    tuple
        DataFrame containing transformed harvest records and
        a dictionary with the new cursor value.
    """

    harvests = read_latest_raw_parquet(
        spark,
        HARVESTS_PATH,
        "id",
    )

    if cursor:
        harvests = harvests.filter(col("updated_at") > cursor["updated_at"])

    dates = read_clickhouse(
        spark,
        "dim_date",
    ).select(
        "date_key",
        "full_date",
    )

    times = read_clickhouse(
        spark,
        "dim_time",
    ).select(
        "time_key",
        "hour",
        "minute",
    )

    farms = (
        read_clickhouse(
            spark,
            "dim_farm",
        )
        .filter(col("is_current") == 1)
        .select(
            "farm_id",
            "farm_key",
        )
    )

    crops = read_clickhouse(
        spark,
        "dim_crop",
    ).select(
        "crop_id",
    )

    quality = read_clickhouse(
        spark,
        "dim_quality_grade",
    ).select(
        "quality_grade_id",
    )

    df = (
        harvests.alias("h")
        .withColumn(
            "harvest_key",
            xxhash64(concat_ws("|", col("h.farm_id"), col("h.id"))).cast("long"),
        )
        .withColumn(
            "harvested_at",
            from_unixtime(col("h.created_at")).cast("timestamp"),
        )
        .withColumn(
            "harvest_date",
            to_date(col("harvested_at")),
        )
        .withColumn(
            "harvest_hour",
            hour(col("harvested_at")),
        )
        .withColumn(
            "harvest_minute",
            minute(col("harvested_at")),
        )
        .join(
            farms.alias("f"),
            col("h.farm_id") == col("f.farm_id"),
            "left",
        )
        .join(
            crops.alias("c"),
            col("h.crop_id") == col("c.crop_id"),
            "left",
        )
        .join(
            quality.alias("q"),
            col("h.quality_grade_id") == col("q.quality_grade_id"),
            "left",
        )
        .join(
            dates.alias("d"),
            col("harvest_date") == col("d.full_date"),
            "left",
        )
        .join(
            times.alias("t"),
            (col("harvest_hour") == col("t.hour"))
            & (col("harvest_minute") == col("t.minute")),
            "left",
        )
        .select(
            col("harvest_key"),
            col("h.id").cast("long").alias("harvest_id"),
            col("f.farm_key").alias("farm_key"),
            col("h.farm_id").cast("long").alias("farm_id"),
            col("h.crop_id").cast("long").alias("crop_id"),
            col("q.quality_grade_id").cast("long").alias("quality_grade_id"),
            col("d.date_key").alias("date_key"),
            col("t.time_key").alias("time_key"),
            col("harvested_at"),
            col("harvest_date"),
            col("h.weight_kg").cast("decimal(10,3)").alias("weight_kg"),
        )
    )

    cursor_row = harvests.select(spark_max("updated_at").alias("updated_at")).collect()[
        0
    ]

    new_cursor = {"updated_at": cursor_row["updated_at"]}

    return df, new_cursor
