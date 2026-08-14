"""Read-only tools the model drives.

Plain functions that take the ClickHouse client, so they can be tested with a
mock and wired as `@mcp.tool` handlers separately.

None of them raise. Every failure comes back as {"error": {"code", "message"}},
because the model has to read the failure and correct itself - an exception
would surface as an MCP transport error it can do nothing with.
"""

from typing import Any

from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import ClickHouseError

from app.config import get_settings
from app.sql_safety import SQLSafetyError, validate_and_rewrite_sql

# The model may only look at the warehouse. system.* stays reachable to these
# tools internally, but not through anything the model names itself.
ALLOWED_DATABASES = frozenset({"urbangreen_dw", "etl"})

DEFAULT_DATABASE = "urbangreen_dw"


def list_tables(client: Client, database: str = DEFAULT_DATABASE) -> dict[str, Any]:
    """List the tables in a warehouse database.

    Args:
        client: ClickHouse client to query through.
        database: Database to list. Must be one of ALLOWED_DATABASES.

    Returns:
        dict: ``{"database", "tables", "table_count"}``, or an error payload.
    """

    denied = _reject_unknown_database(database)
    if denied is not None:
        return denied

    try:
        result = client.query(
            "SELECT name FROM system.tables WHERE database = {database:String} ORDER BY name",
            parameters={"database": database},
        )
    except ClickHouseError as error:
        return _clickhouse_error(error)

    tables = [row[0] for row in result.result_rows]

    return {"database": database, "tables": tables, "table_count": len(tables)}


def describe_table(
    client: Client,
    table: str,
    database: str = DEFAULT_DATABASE,
) -> dict[str, Any]:
    """Describe the columns of a warehouse table.

    Args:
        client: ClickHouse client to query through.
        table: Table to describe.
        database: Database the table lives in. Must be one of ALLOWED_DATABASES.

    Returns:
        dict: ``{"database", "table", "columns"}``, or an error payload.
    """

    denied = _reject_unknown_database(database)
    if denied is not None:
        return denied

    if not table or not table.strip():
        return _error("TABLE_NOT_FOUND", "No table name was given.")

    table = table.strip()

    try:
        # system.columns rather than DESCRIBE TABLE: DESCRIBE takes an
        # identifier, which cannot be bound as a parameter, so it would force
        # string interpolation of a model-supplied name.
        result = client.query(
            "SELECT name, type, default_kind, default_expression, comment "
            "FROM system.columns "
            "WHERE database = {database:String} AND table = {table:String} "
            "ORDER BY position",
            parameters={"database": database, "table": table},
        )
    except ClickHouseError as error:
        return _clickhouse_error(error)

    if not result.result_rows:
        return _error(
            "TABLE_NOT_FOUND",
            f"Table '{table}' does not exist in database '{database}'. "
            "Call list_tables to see what is available.",
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

    return {"database": database, "table": table, "columns": columns}


def execute_query(client: Client, sql: str, limit: int | None = None) -> dict[str, Any]:
    """Run a read-only query through the SQL safety layer.

    Args:
        client: ClickHouse client to query through.
        sql: Statement to run. Validated and rewritten before execution.
        limit: Row limit to apply when the statement carries none. Clamped to
            the configured ceiling.

    Returns:
        dict: ``{"sql", "limit", "columns", "rows", "row_count", "truncated"}``,
        or an error payload.
    """

    settings = get_settings()
    max_limit = settings.max_row_limit

    if limit is None:
        default_limit = settings.default_row_limit
    elif limit < 1:
        return _error("INVALID_LIMIT", "The limit must be a positive whole number.")
    else:
        default_limit = min(limit, max_limit)

    try:
        rewritten_sql, applied_limit = validate_and_rewrite_sql(
            sql,
            default_limit=default_limit,
            max_limit=max_limit,
        )
    except SQLSafetyError as error:
        return _error(error.code, error.message)

    try:
        result = client.query(rewritten_sql)
    except ClickHouseError as error:
        return _clickhouse_error(error)

    rows = [list(row) for row in result.result_rows]

    return {
        "sql": rewritten_sql,
        "limit": applied_limit,
        "columns": list(result.column_names),
        "rows": rows,
        "row_count": len(rows),
        # Only claim truncation when a row limit was actually written into the
        # SQL. A limit of 0 means none applies, and None means the statement
        # carries one we could not read, so neither says anything about the
        # result being cut short.
        "truncated": bool(applied_limit) and len(rows) >= applied_limit,
    }


def _reject_unknown_database(database: str) -> dict[str, Any] | None:
    """Return an error payload when the database is outside the allow-list."""

    if database in ALLOWED_DATABASES:
        return None

    allowed = ", ".join(sorted(ALLOWED_DATABASES))

    return _error(
        "DATABASE_NOT_ALLOWED",
        f"Database '{database}' is not available. Allowed databases: {allowed}.",
    )


def _clickhouse_error(error: ClickHouseError) -> dict[str, Any]:
    """Turn a driver or server-side failure into an error payload."""

    return _error("CLICKHOUSE_ERROR", " ".join(str(error).split()))


def _error(code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}
