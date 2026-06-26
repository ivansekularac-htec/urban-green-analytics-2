from __future__ import annotations

import re
from datetime import datetime, timezone

from extract_common.settings import MINIO_STAGING_PREFIX


def build_table_object_key(
    table: str,
    previous_cursor: dict[str, int],
    upper_cursor: dict[str, int],
) -> str:
    range_path = build_range_path(
        previous_cursor=previous_cursor,
        upper_cursor=upper_cursor,
    )

    return f"{MINIO_STAGING_PREFIX}/{table}/{range_path}/{table}.parquet"


def build_partitioned_object_key(
    table: str,
    partition_name: str,
    partition_value: str,
    previous_cursor: dict[str, int],
    upper_cursor: dict[str, int],
) -> str:
    range_path = build_range_path(
        previous_cursor=previous_cursor,
        upper_cursor=upper_cursor,
    )
    safe_partition_value = safe_object_key_value(partition_value)

    return (
        f"{MINIO_STAGING_PREFIX}/{table}/"
        f"{partition_name}={safe_partition_value}/"
        f"{range_path}/{table}.parquet"
    )


def build_range_path(previous_cursor: dict[str, int], upper_cursor: dict[str, int]) -> str:
    return (
        f"from_updated_at={format_epoch(previous_cursor['updated_at'])}"
        f"_id={previous_cursor['id']}/"
        f"to_updated_at={format_epoch(upper_cursor['updated_at'])}"
        f"_id={upper_cursor['id']}"
    )


def format_epoch(value: int) -> str:
    return datetime.fromtimestamp(int(value), tz=timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def safe_object_key_value(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.=-]", "_", value)