def build_object_key(
    table,
    cursor_start,
    cursor_end,
    partition_column=None,
    partition_value=None,
):
    """
    Builds the destination object key for a Parquet file.

    General tables:
        farms/updated_at=100_200.parquet

    Partitioned tables:
        harvests/created_at=2026-06-26/updated_at=100_200.parquet
    """

    filename = f"updated_at={cursor_start}_{cursor_end}.parquet"

    if partition_column and partition_value:
        return f"{table}/{partition_column}={partition_value}/{filename}"

    return f"{table}/{filename}"
