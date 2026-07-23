"""Reshaping helpers shared by the warehouse loaders."""

from pyspark.sql import Window
from pyspark.sql import functions as F


def epoch_to_ts(column):
    """Convert a source audit timestamp to a real timestamp.

    The application stores created_at / updated_at as Unix epoch seconds, so
    the value has to be converted before it can be compared with warehouse
    DateTime64 columns or used as an SCD2 validity bound.
    """
    return F.col(column).cast("long").cast("timestamp")


def latest_per_key(df, key, order_by="updated_at"):
    """Keep only the newest source row per key.

    The extractor writes one folder per run window and a row reappears in every
    window in which it changed, so the raw zone holds several versions of the
    same entity. A Type 1 dimension stores only the current state, so the
    loader collapses those versions here rather than relying on the
    ReplacingMergeTree merge, whose timing is not guaranteed at read time.
    """
    window = Window.partitionBy(key).orderBy(F.col(order_by).desc())
    return (
        df.withColumn("_row", F.row_number().over(window))
        .filter(F.col("_row") == 1)
        .drop("_row")
    )
