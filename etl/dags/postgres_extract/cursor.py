from __future__ import annotations

from airflow.sdk import Variable

POSTGRES_CONN_ID = "urbangreen_db"
MINIO_CONN_ID = "urbangreen_minio"

SCHEMA = "app"
CURSOR_COLUMN = "updated_at"
PRIMARY_KEY = "id"

DEFAULT_CURSOR: dict[str, str | None] = {"updated_at": None, "id": None}


def _cursor_key(table: str) -> str:
    return f"extract_cursor__{table}"


def get_cursor(table: str) -> dict[str, str] | None:
    """Read the per-table cursor from Airflow Variables."""
    raw = Variable.get(
        _cursor_key(table),
        default=None,
        deserialize_json=True,
    )

    if not isinstance(raw, dict):
        return DEFAULT_CURSOR.copy()

    return {
        "updated_at": raw.get("updated_at"),
        "id": raw.get("id"),
    }


def set_cursor(table: str, cursor: dict[str, str]) -> None:
    Variable.set(_cursor_key(table), cursor, serialize_json=True)


def _run_cutoff(pg) -> int:
    """Newest updated_at we are willing to read this run."""
    value = pg.get_first(
        "SELECT EXTRACT(EPOCH FROM CURRENT_TIMESTAMP)::BIGINT",
    )[0]
    return max(int(value), 0)


def _high_watermark(
    pg,
    table: str,
    low: dict[str, str] | None,
    run_cutoff: int,
) -> dict[str, str] | None:
    """Snapshot the newest (updated_at, id) in the window since the last cursor."""
    conditions = []
    parameters = []

    if low and low.get("updated_at") is not None:
        conditions.append(
            f"({CURSOR_COLUMN} > %s OR ({CURSOR_COLUMN} = %s AND {PRIMARY_KEY} > %s))"
        )
        parameters.extend([low["updated_at"], low["updated_at"], low["id"] or "0"])

    conditions.append(f"{CURSOR_COLUMN} <= %s")
    parameters.append(run_cutoff)

    where_clause = " AND ".join(conditions)

    row = pg.get_first(
        f"""
        SELECT {CURSOR_COLUMN}, {PRIMARY_KEY}
        FROM {SCHEMA}.{table}
        WHERE {where_clause}
        ORDER BY {CURSOR_COLUMN} DESC, {PRIMARY_KEY} DESC
        LIMIT 1
        """,
        parameters=tuple(parameters),
    )

    if row is None:
        return None

    return {"updated_at": str(row[0]), "id": str(row[1])}
