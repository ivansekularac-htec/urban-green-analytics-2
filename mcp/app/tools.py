"""
Core read-only ClickHouse tools for the MCP service.

Provides table discovery, schema inspection, and safe query execution
with structured model-readable results and errors.
"""

from __future__ import annotations

from typing import Any

from clickhouse_connect.driver.client import Client

from app.config import get_settings
from app.sql_safety import SQLSafetyError, validate_and_rewrite_sql

ALLOWED_DATABASES = frozenset({"urbangreen_dw", "etl"})


def list_tables(
    client: Client,
    database: str = "urbangreen_dw",
) -> dict[str, Any]:
    """Return tables from an allowed warehouse database."""

    if database not in ALLOWED_DATABASES:
        return _error(
            "DATABASE_NOT_ALLOWED",
            (
                f"Database '{database}' is not allowed. "
                f"Allowed databases: {', '.join(sorted(ALLOWED_DATABASES))}."
            ),
        )

    try:
        # Use bound parameters instead of interpolating database names into SQL.
        result = client.query(
            """
            SELECT name
            FROM system.tables
            WHERE database = {database:String}
            ORDER BY name
            """,
            parameters={
                "database": database,
            },
        )
    except Exception as exc:
        return _clickhouse_error(exc)

    return {
        "database": database,
        "tables": [row[0] for row in result.result_rows],
    }


def describe_table(
    client: Client,
    table: str,
    database: str = "urbangreen_dw",
) -> dict[str, Any]:
    """Return column metadata for a table in an allowed database."""

    if database not in ALLOWED_DATABASES:
        return _error(
            "DATABASE_NOT_ALLOWED",
            (
                f"Database '{database}' is not allowed. "
                f"Allowed databases: {', '.join(sorted(ALLOWED_DATABASES))}."
            ),
        )

    try:
        # Bind both database and table names when querying system metadata.
        result = client.query(
            """
            SELECT
                name,
                type,
                default_kind,
                default_expression,
                comment
            FROM system.columns
            WHERE database = {database:String}
              AND table = {table:String}
            ORDER BY position
            """,
            parameters={
                "database": database,
                "table": table,
            },
        )
    except Exception as exc:
        return _clickhouse_error(exc)

    if not result.result_rows:
        return _error(
            "TABLE_NOT_FOUND",
            f"Table '{database}.{table}' does not exist.",
        )

    columns = [
        {
            "name": row[0],
            "type": row[1],
            "default_kind": row[2],
            "default_expression": row[3],
            "comment": row[4],
        }
        for row in result.result_rows
    ]

    return {
        "database": database,
        "table": table,
        "columns": columns,
    }


def execute_query(
    client: Client,
    sql: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """Validate and execute a read-only ClickHouse query."""

    settings = get_settings()

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            return _error(
                "INVALID_LIMIT",
                "Limit must be a positive integer.",
            )

        # A caller-supplied limit cannot exceed the service-wide maximum.
        requested_limit = min(
            limit,
            settings.max_row_limit,
        )

        default_limit = requested_limit
        max_limit = requested_limit

    else:
        default_limit = settings.default_row_limit
        max_limit = settings.max_row_limit

    try:
        rewritten_sql, applied_limit = validate_and_rewrite_sql(
            sql,
            default_limit=default_limit,
            max_limit=max_limit,
        )
    except SQLSafetyError as exc:
        return _error(
            exc.code,
            exc.message,
        )
    except ValueError as exc:
        return _error(
            "INVALID_CONFIGURATION",
            str(exc),
        )

    try:
        result = client.query(rewritten_sql)
    except Exception as exc:
        return _clickhouse_error(exc)

    rows = list(result.result_rows)
    row_count = result.row_count

    # Meeting the applied limit may mean additional rows were available.
    truncated = applied_limit is not None and applied_limit > 0 and row_count >= applied_limit

    return {
        "sql": rewritten_sql,
        "limit": applied_limit,
        "columns": list(result.column_names),
        "rows": rows,
        "row_count": row_count,
        "truncated": truncated,
    }


def _error(
    code: str,
    message: str,
) -> dict[str, Any]:
    """Build a model-readable error payload."""

    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


def _clickhouse_error(exc: Exception) -> dict[str, Any]:
    """Convert a ClickHouse failure into a structured error payload."""

    return _error(
        "CLICKHOUSE_ERROR",
        str(exc),
    )
