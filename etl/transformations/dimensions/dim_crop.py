"""
Creates dim_crop dimension from raw PostgreSQL parquet data.

The loader performs a full refresh on every run.
All available raw parquet files are read, and the latest version
of each crop and crop category is selected based on the ingestion
batch timestamp.

The resulting dataframe represents the current state of the dimension
and is written to ClickHouse.
"""

from common.config import RAW_POSTGRES_PATH
from common.raw import read_latest_raw_parquet
from pyspark.sql.functions import (
    current_timestamp,
)

CROPS_PATH = f"{RAW_POSTGRES_PATH}/crops/"
CROP_CATEGORIES_PATH = f"{RAW_POSTGRES_PATH}/crop_categories/"


def create_dim_crop(spark):
    """
    Creates the latest state of the dim_crop dimension.

    The function reads raw crop and crop category data,
    keeps the latest record for each primary key, and builds
    the dimension dataframe used for loading into ClickHouse.

    Returns
    -------
    DataFrame
        Dimension dataframe containing one latest row per crop.
    """

    crops = read_latest_raw_parquet(
        spark,
        CROPS_PATH,
        "id",
    )

    crop_categories = read_latest_raw_parquet(
        spark,
        CROP_CATEGORIES_PATH,
        "id",
    )

    dim_crop_df = crops.join(
        crop_categories, crops.category_id == crop_categories.id, "left"
    ).select(
        crops.id.cast("long").alias("crop_id"),
        crops.name.alias("name"),
        crops.description.alias("description"),
        crops.category_id.cast("long").alias("crop_category_id"),
        crop_categories.name.alias("category_name"),
        current_timestamp().alias("_loaded_at"),
    )

    return dim_crop_df
