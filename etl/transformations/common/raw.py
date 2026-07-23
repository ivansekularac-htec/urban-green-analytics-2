"""
Raw data readers used by ETL pipelines.

This module contains readers for different ingestion patterns:

- PostgreSQL parquet extracts:
    Snapshot-based ingestion with latest-record selection.

- Kafka parquet events:
    Append-only event ingestion using event-date cursors.
"""

from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    input_file_name,
    regexp_extract,
    row_number,
)
from pyspark.sql.window import Window


def read_raw_parquet(
    spark,
    path: str,
) -> DataFrame:
    """
    Reads raw parquet data from S3A/MinIO.

    Raw ingestion folders follow the pattern:

    <start_timestamp>__<end_timestamp>/

    Example:

    19700101T000000Z__20260721T104809Z/

    The end timestamp is extracted and stored as `_batch_end`.

    Parameters
    ----------
    spark:
        Active SparkSession.

    path:
        S3A path containing parquet files.

    Returns
    -------
    DataFrame
        Raw dataframe enriched with:

        _source_file
            Full source parquet file path.

        _batch_end
            Raw ingestion batch end timestamp.
    """

    return (
        spark.read.option("recursiveFileLookup", "true")
        .parquet(path)
        .withColumn("_source_file", input_file_name())
        .withColumn(
            "_batch_end", regexp_extract("_source_file", r"__(\d{8}T\d{6}Z)/", 1)
        )
    )


def read_latest_raw_parquet(
    spark,
    path: str,
    business_key: str,
) -> DataFrame:
    """
    Reads raw parquet data and keeps only the latest record per business key.

    Raw datasets may contain multiple versions of the same business entity
    because data is ingested incrementally in batches. This function performs
    a deduplication step by selecting the record with the newest ingestion
    batch timestamp for each business key.

    The latest record is determined using the ``_batch_end`` metadata column
    created by :func:`read_raw_parquet`.

    Parameters
    ----------
    spark : SparkSession
        Active Spark session used for reading parquet files.

    path : str
        S3A/MinIO path containing raw parquet files.

    business_key : str
        Column name identifying a unique business entity.
        Example:
            "crop_id"

    Returns
    -------
    DataFrame
        DataFrame containing only the latest version of each business entity.

        The temporary ranking column ``_rn`` used for deduplication is removed
        before returning the result.

    Raises
    ------
    AnalysisException
        If the source path cannot be read or the business key column does not
        exist.
    """

    df = read_raw_parquet(
        spark,
        path,
    )

    window = Window.partitionBy(business_key).orderBy(
        col("_batch_end").desc(),
    )

    return (
        df.withColumn(
            "_rn",
            row_number().over(window),
        )
        .filter(col("_rn") == 1)
        .drop("_rn")
    )


def read_latest_raw_batch(
    spark,
    base_path,
    last_batch=None,
):
    """
    Reads the latest available raw parquet batch incrementally.

    Raw ingestion data is stored in timestamped batch folders.
    The function discovers available batches, filters already processed
    batches using the stored cursor, and returns only the newest batch.

    This reader is used for sources where ingestion is organized by
    extraction batch rather than individual entity versions.

    Parameters
    ----------
    spark:
        Active SparkSession.

    base_path:
        Base S3A/MinIO path containing ingestion batch folders.

    last_batch:
        Previously processed batch identifier.
        Only batches newer than this value are considered.

    Returns
    -------
    tuple
        DataFrame
            Raw dataframe from the latest available batch.

        str
            Identifier of the processed batch used as the next cursor.

        Returns:
            (None, None) when no new batch is available.
    """

    fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(
        spark._jsc.hadoopConfiguration()
    )

    path = spark._jvm.org.apache.hadoop.fs.Path(base_path)

    batches = [str(x.getPath()) for x in fs.listStatus(path) if x.isDirectory()]

    batches = sorted(batches)

    if last_batch:
        batches = [b for b in batches if b.split("/")[-1] > last_batch]

    if not batches:
        return None, None

    latest_batch = batches[-1]

    df = spark.read.parquet(latest_batch)

    return df, latest_batch.split("/")[-1]


def read_kafka_raw_parquet(
    spark,
    base_path,
    last_event_date=None,
):
    """
    Reads raw Kafka parquet sensor events incrementally.

    Kafka ingestion stores events partitioned by event_date:

        sensor_readings/
            event_date=YYYY-MM-DD/
                part-*.parquet

    The function loads available sensor events and optionally filters
    partitions newer than the last processed event date.

    Parameters
    ----------
    spark:
        Active SparkSession.

    base_path:
        S3A/MinIO path containing Kafka parquet partitions.

    last_event_date:
        Previously processed event date cursor.
        Only newer partitions are returned.

    Returns
    -------
    DataFrame
        Raw sensor event dataframe ready for transformation.
    """

    df = spark.read.parquet(base_path)

    if last_event_date:
        df = df.filter(col("event_date") > last_event_date)

    return df
