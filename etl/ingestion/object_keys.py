from ingestion.config import OBJECT_PREFIX


def build_object_key(
    table,
    start_cursor,
    end_cursor,
    partition_column=None,
    partition_value=None,
):
    """
    Builds a deterministic object key for a Parquet ingestion batch.

    Each file name encodes the cursor range processed by a single batch,
    making the output traceable and idempotent.

    Non-partitioned layout:

        {OBJECT_PREFIX}/{table}/updated_at={start}_{end}.parquet

    Partitioned layout:

        {OBJECT_PREFIX}/{table}/{partition_column}={partition_value}/
            updated_at={start}_{end}.parquet

    Example:

        raw/postgres/
            harvests/
                created_at=2024-06-10/
                    updated_at=1717977600-125_1717981200-418.parquet
    """

    # ---------------------------------------------------------
    # Encode the cursor range in the filename.
    # Each extraction batch produces a unique object.
    # ---------------------------------------------------------
    filename = (
        f"updated_at="
        f"{start_cursor['updated_at']}-{start_cursor['id']}_"
        f"{end_cursor['updated_at']}-{end_cursor['id']}.parquet"
    )

    # ---------------------------------------------------------
    # Build the common object prefix.
    # This namespaces objects by ingestion source (e.g. raw/postgres)
    # to avoid collisions with future pipelines such as Kafka.
    # ---------------------------------------------------------
    base_path = f"{OBJECT_PREFIX}/{table}"

    # ---------------------------------------------------------
    # Partitioned layout
    # ---------------------------------------------------------
    if partition_column and partition_value:
        return f"{base_path}/{partition_column}={partition_value}/{filename}"

    # ---------------------------------------------------------
    # Non-partitioned layout
    # ---------------------------------------------------------
    return f"{base_path}/{filename}"
