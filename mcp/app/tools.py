"""Plain, read-only ClickHouse tools intended for MCP handlers."""

from typing import Any

from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import ClickHouseError

from app.config import get_settings
from app.sql_safety import SQLSafetyError, validate_and_rewrite_sql

ALLOWED_DATABASES = frozenset({"urbangreen_dw", "etl"})
DEFAULT_DATABASE = "urbangreen_dw"

_LIST_TABLES_SQL = "SELECT name FROM system.tables WHERE database = {database:String} ORDER BY name"

_DESCRIBE_TABLE_SQL = (
    "SELECT name, type, default_kind, default_expression, comment "
    "FROM system.columns "
    "WHERE database = {database:String} "
    "AND table = {table:String} "
    "ORDER BY position"
)


def list_tables(
    client: Client,
    database: str = DEFAULT_DATABASE,
) -> dict[str, Any]:
    """Return the tables in an allowed warehouse database."""

    database_error = _validate_database(database)
    if database_error is not None:
        return database_error

    try:
        result = client.query(
            _LIST_TABLES_SQL,
            parameters={"database": database},
        )
    except ClickHouseError as error:
        return _clickhouse_error(error)

    tables = [row[0] for row in result.result_rows]

    return {
        "database": database,
        "tables": tables,
        "table_count": len(tables),
    }


def describe_table(
    client: Client,
    table: str,
    database: str = DEFAULT_DATABASE,
) -> dict[str, Any]:
    """Return column metadata for a table in an allowed database."""

    database_error = _validate_database(database)
    if database_error is not None:
        return database_error

    table = table.strip()
    if not table:
        return _error(
            code="TABLE_NOT_FOUND",
            message="A table name is required. Call list_tables to see available tables.",
        )

    try:
        result = client.query(
            _DESCRIBE_TABLE_SQL,
            parameters={
                "database": database,
                "table": table,
            },
        )
    except ClickHouseError as error:
        return _clickhouse_error(error)

    if not result.result_rows:
        return _error(
            code="TABLE_NOT_FOUND",
            message=(
                f"Table '{database}.{table}' was not found. "
                "Call list_tables to see available tables."
            ),
        )

    columns = [
        {
            "name": name,
            "type": type_,
            "default_kind": default_kind or None,
            "default_expression": default_expression or None,
            "comment": comment or None,
        }
        for name, type_, default_kind, default_expression, comment in result.result_rows
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
    """Validate, limit, and execute one read-only ClickHouse query."""

    settings = get_settings()

    if limit is not None and (not isinstance(limit, int) or isinstance(limit, bool) or limit < 1):
        return _error(
            code="INVALID_LIMIT",
            message="The limit must be a positive integer.",
        )

    requested_limit = settings.default_row_limit if limit is None else limit
    requested_limit = min(requested_limit, settings.max_row_limit)

    try:
        rewritten_sql, applied_limit = validate_and_rewrite_sql(
            sql,
            default_limit=requested_limit,
            max_limit=settings.max_row_limit,
        )
    except SQLSafetyError as error:
        return _error(code=error.code, message=error.message)
    except ValueError as error:
        return _error(code="INVALID_LIMIT_CONFIGURATION", message=str(error))

    try:
        result = client.query(rewritten_sql)
    except ClickHouseError as error:
        return _clickhouse_error(error)

    rows = [list(row) for row in result.result_rows]
    row_count = len(rows)

    return {
        "sql": rewritten_sql,
        "limit": applied_limit,
        "columns": list(result.column_names),
        "rows": rows,
        "row_count": row_count,
        "truncated": bool(applied_limit) and row_count >= applied_limit,
    }


def _validate_database(database: str) -> dict[str, Any] | None:
    if database in ALLOWED_DATABASES:
        return None

    allowed = ", ".join(sorted(ALLOWED_DATABASES))

    return _error(
        code="DATABASE_NOT_ALLOWED",
        message=f"Database '{database}' is not available. Allowed databases: {allowed}.",
    )


def _clickhouse_error(error: ClickHouseError) -> dict[str, Any]:
    message = " ".join(str(error).split())
    return _error(code="CLICKHOUSE_ERROR", message=message)


def _error(code: str, message: str) -> dict[str, Any]:
    return {
        "error": {
            "code": code,
            "message": message,
        }
    }
