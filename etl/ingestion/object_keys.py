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

        {table}/updated_at={start}_{end}.parquet

    Partitioned layout:

        {table}/{partition_column}={partition_value}/
            updated_at={start}_{end}.parquet

    Example:

        harvests/
            created_at=2024-06-10/
                updated_at=1717977600_1717981200.parquet
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
    # Partitioned layout
    # ---------------------------------------------------------
    if partition_column and partition_value:
        return f"{table}/{partition_column}={partition_value}/{filename}"

    # ---------------------------------------------------------
    # Non-partitioned layout
    # ---------------------------------------------------------
    return f"{table}/{filename}"
