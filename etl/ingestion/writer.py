import pandas as pd

from ingestion.object_keys import build_object_key
from ingestion.storage import upload_parquet


def write_dataframe(df, config, cursor_start, cursor_end):
    """
    Writes a DataFrame to MinIO.

    If a partition_column is configured, one Parquet file is written
    per partition value. Otherwise, a single Parquet file is written.
    """

    table = config["table"]
    bucket = config["bucket"]
    partition_column = config.get("partition_column")

    # ---------------------------------
    # Non-partitioned tables
    # ---------------------------------

    if partition_column is None:
        parquet_path = f"/tmp/{table}_{cursor_end}.parquet"

        df.to_parquet(parquet_path, index=False)

        object_key = build_object_key(
            table=table,
            cursor_start=cursor_start,
            cursor_end=cursor_end,
        )

        upload_parquet(
            parquet_path=parquet_path,
            bucket=bucket,
            object_key=object_key,
        )

        return

    # ---------------------------------
    # Partitioned tables
    # ---------------------------------

    # Create a copy so we don't modify the caller's DataFrame
    partitioned_df = df.copy()

    partitioned_df["_partition_date"] = pd.to_datetime(
        partitioned_df[partition_column],
        unit="s",
        utc=True,
    ).dt.strftime("%Y-%m-%d")

    for partition_date, partition_df in partitioned_df.groupby("_partition_date"):
        parquet_path = (
            f"/tmp/{table}_{partition_date}_{cursor_start}_{cursor_end}.parquet"
        )

        partition_df = partition_df.drop(columns="_partition_date")

        partition_df.to_parquet(
            parquet_path,
            index=False,
        )

        object_key = build_object_key(
            table=table,
            cursor_start=cursor_start,
            cursor_end=cursor_end,
            partition_column=partition_column,
            partition_value=partition_date,
        )

        print(f"Uploading partition {partition_date}")

        upload_parquet(
            parquet_path=parquet_path,
            bucket=bucket,
            object_key=object_key,
        )

        print(f"Uploaded partition {partition_date}")
