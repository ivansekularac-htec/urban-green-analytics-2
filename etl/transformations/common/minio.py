import re
from datetime import datetime, timezone

from pyspark.sql import DataFrame, SparkSession, Window
from pyspark.sql import functions as F

BATCH_PATTERN = re.compile(r"^\d{8}T\d{6}Z__(\d{8}T\d{6}Z)$")


def find_new_batches(
    spark: SparkSession,
    table_path: str,
    last_watermark: int,
) -> tuple[list[str], int]:
    """Return paths of batches newer than the current watermark and the newest discovered watermark."""

    root_path = spark._jvm.org.apache.hadoop.fs.Path(table_path)

    filesystem = root_path.getFileSystem(spark._jsc.hadoopConfiguration())

    if not filesystem.exists(root_path):
        raise FileNotFoundError(f"MinIO path does not exist: {table_path}")

    batches: list[tuple[int, str]] = []

    for status in filesystem.listStatus(root_path):
        if not status.isDirectory():
            continue

        directory_path = status.getPath()
        directory_name = directory_path.getName()

        match = BATCH_PATTERN.fullmatch(directory_name)

        if match is None:
            continue

        batch_end = datetime.strptime(
            match.group(1),
            "%Y%m%dT%H%M%SZ",
        ).replace(tzinfo=timezone.utc)

        batch_end_epoch = int(batch_end.timestamp())

        if batch_end_epoch > last_watermark:
            batches.append(
                (
                    batch_end_epoch,
                    directory_path.toString(),
                )
            )

    batches.sort()

    paths = [path for _, path in batches]

    new_watermark = max(
        (watermark for watermark, _ in batches),
        default=last_watermark,
    )

    return paths, new_watermark


def read_batches(
    spark: SparkSession,
    paths: list[str],
) -> DataFrame:
    """Read selected Parquet batch directories."""

    return spark.read.parquet(*paths)


def read_full_table(
    spark: SparkSession,
    table_path: str,
) -> DataFrame:
    """Read all Parquet batches of a small source table."""

    return spark.read.option("recursiveFileLookup", "true").parquet(table_path)


def latest_rows(
    dataframe: DataFrame,
) -> DataFrame:
    """Return the current row for every source id."""

    window = Window.partitionBy("id").orderBy(F.col("updated_at").desc())

    return (
        dataframe.withColumn(
            "_row_number",
            F.row_number().over(window),
        )
        .filter(F.col("_row_number") == 1)
        .drop("_row_number")
    )
