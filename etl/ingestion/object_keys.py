def build_object_key(
    table,
    cursor_start,
    cursor_end,
    partition_column=None,
    partition_value=None,
):
    """
    Builds a deterministic S3/MinIO object key for Parquet ingestion output.

    This ensures:
        - traceable ingestion ranges
        - idempotent writes (same input → same key)
        - optional partitioning for high-volume tables

    Key structure:

        Non-partitioned:
            {table}/updated_at={start}_{end}.parquet

        Partitioned:
            {table}/{partition_column}={partition_value}/updated_at={start}_{end}.parquet

    Example:
        harvests/created_at=2026-06-26/updated_at=100_200.parquet
    """

    # ---------------------------------------------------------
    # Base filename encodes ingestion range (important for traceability)
    # ---------------------------------------------------------
    filename = f"updated_at={cursor_start}_{cursor_end}.parquet"

    # ---------------------------------------------------------
    # Partitioned layout (used for large/high-volume tables like harvests)
    # ---------------------------------------------------------
    if partition_column and partition_value:
        return f"{table}/{partition_column}={partition_value}/{filename}"

    # ---------------------------------------------------------
    # Default flat layout
    # ---------------------------------------------------------
    return f"{table}/{filename}"
