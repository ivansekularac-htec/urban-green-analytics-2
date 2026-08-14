"""
Core read-only tools for accessing ClickHouse warehouse data.
"""

from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import ClickHouseError

from app.sql_safety import SQLSafetyError, validate_and_rewrite_sql

ALLOWED_DATABASES = {"urbangreen_dw"}


def _validate_database(database: str) -> dict[str, str] | None:
    """Return a model-readable error when a database is not allowed."""
    if database in ALLOWED_DATABASES:
        return None

    allowed = ", ".join(sorted(ALLOWED_DATABASES))

    return {"error": (f"Database '{database}' is not allowed. Allowed databases: {allowed}.")}


def list_tables(client: Client, database: str) -> dict:
    """List tables in an allowed ClickHouse warehouse database."""
    database_error = _validate_database(database)

    if database_error:
        return database_error

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
        return {"error": f"ClickHouse error: {exc}"}

    return {
        "database": database,
        "tables": [row[0] for row in result.result_rows],
    }


def describe_table(client: Client, database: str, table: str) -> dict:
    """Describe columns for a table in an allowed ClickHouse database."""
    database_error = _validate_database(database)

    if database_error:
        return database_error

    try:
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
    except ClickHouseError as exc:
        return {"error": f"ClickHouse error: {exc}"}

    if not result.result_rows:
        return {
            "error": f"Table '{database}.{table}' was not found.",
        }

    return {
        "database": database,
        "table": table,
        "columns": [
            {
                "name": name,
                "type": column_type,
                "default_kind": default_kind,
                "default_expression": default_expression,
                "comment": comment,
            }
            for name, column_type, default_kind, default_expression, comment in result.result_rows
        ],
    }


def execute_query(
    client: Client,
    sql: str,
    *,
    default_limit: int,
    max_limit: int,
    limit: int | None = None,
) -> dict:
    """Validate and execute a read-only ClickHouse query."""
    if limit is not None:
        if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
            return {"error": "Limit must be a positive integer."}

        effective_ceiling = min(limit, max_limit)
        rewrite_default = effective_ceiling
        rewrite_max = effective_ceiling
    else:
        rewrite_default = default_limit
        rewrite_max = max_limit

    try:
        rewritten_sql, applied_limit = validate_and_rewrite_sql(
            sql,
            default_limit=rewrite_default,
            max_limit=rewrite_max,
        )
    except SQLSafetyError as exc:
        return {"error": str(exc)}

    try:
        result = client.query(rewritten_sql)
    except ClickHouseError as exc:
        return {"error": f"ClickHouse error: {exc}"}

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
