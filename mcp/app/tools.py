"""Read-only ClickHouse tools exposed to the MCP layer."""

import logging
from typing import Any

from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import ClickHouseError

from app.config import get_settings
from app.sql_safety import SQLSafetyError, validate_and_rewrite_sql

logger = logging.getLogger(__name__)

_ALLOWED_DATABASES = {"urbangreen_dw"}


def _error(code: str, message: str) -> dict[str, Any]:
    """Build a model-readable error payload."""
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }


def list_tables(
    client: Client,
    database: str = "urbangreen_dw",
) -> dict[str, Any]:
    """Return tables from an allowed warehouse database."""
    if database not in _ALLOWED_DATABASES:
        return _error(
            "INVALID_DATABASE",
            (
                f"Database '{database}' is not available. "
                f"Allowed databases: {', '.join(sorted(_ALLOWED_DATABASES))}."
            ),
        )

    try:
        result = client.query(
            """
            SELECT name
            FROM system.tables
            WHERE database = {database:String}
            ORDER BY name
            """,
            parameters={"database": database},
        )
    except ClickHouseError as exc:
        return _error("CLICKHOUSE_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error while listing tables.")
        return _error(
            "INTERNAL_ERROR",
            "Unexpected error while listing tables.",
        )

    return {
        "database": database,
        "tables": [row[0] for row in result.result_rows],
    }


def describe_table(
    client: Client,
    table: str,
    database: str = "urbangreen_dw",
) -> dict[str, Any]:
    """Return column metadata for a table in an allowed warehouse database."""
    if database not in _ALLOWED_DATABASES:
        return _error(
            "INVALID_DATABASE",
            (
                f"Database '{database}' is not available. "
                f"Allowed databases: {', '.join(sorted(_ALLOWED_DATABASES))}."
            ),
        )

    try:
        result = client.query(
            """
            SELECT
                name,
                type,
                default_kind,
                default_expression,
                comment,
                is_in_primary_key,
                is_in_sorting_key,
                is_in_partition_key
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
    except ClickHouseError as exc:
        return _error("CLICKHOUSE_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error while describing table.")
        return _error(
            "INTERNAL_ERROR",
            "Unexpected error while describing table.",
        )

    if not result.result_rows:
        return _error(
            "TABLE_NOT_FOUND",
            f"Table '{table}' was not found in database '{database}'.",
        )

    return {
        "database": database,
        "table": table,
        "columns": [
            {
                "name": row[0],
                "type": row[1],
                "default_kind": row[2],
                "default_expression": row[3],
                "comment": row[4],
                "is_primary_key": bool(row[5]),
                "is_sorting_key": bool(row[6]),
                "is_partition_key": bool(row[7]),
            }
            for row in result.result_rows
        ],
    }


def execute_query(
    client: Client,
    sql: str,
    limit: int | None = None,
) -> dict[str, Any]:
    """Validate and execute a read-only SQL query."""
    try:
        settings = get_settings()
    except Exception:
        logger.exception("Unexpected error while loading query settings.")
        return _error(
            "INTERNAL_ERROR",
            "Unexpected error while loading query settings.",
        )

    if limit is not None:
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            return _error(
                "INVALID_LIMIT",
                "Limit must be a positive integer.",
            )

        query_limit = min(limit, settings.max_row_limit)
        default_limit = query_limit
        max_limit = query_limit
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
        return _error(exc.code, exc.message)
    except Exception:
        logger.exception("Unexpected error while validating query.")
        return _error(
            "INTERNAL_ERROR",
            "Unexpected error while validating query.",
        )

    try:
        result = client.query(rewritten_sql)
    except ClickHouseError as exc:
        return _error("CLICKHOUSE_ERROR", str(exc))
    except Exception:
        logger.exception("Unexpected error while executing query.")
        return _error(
            "INTERNAL_ERROR",
            "Unexpected error while executing query.",
        )

    rows = result.result_rows
    row_count = len(rows)

    truncated = applied_limit is not None and applied_limit > 0 and row_count >= applied_limit

    return {
        "sql": rewritten_sql,
        "limit": applied_limit,
        "columns": list(result.column_names),
        "rows": rows,
        "row_count": row_count,
        "truncated": truncated,
    }
