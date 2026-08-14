"""
Core read-only tools for accessing ClickHouse warehouse data.

The functions in this module provide a small, model-facing data access layer
over ClickHouse. They expose warehouse metadata and read-only query execution
while enforcing database restrictions, SQL safety rules, and configured row
limits.

Errors are returned as structured dictionaries instead of being raised so that
LLM callers can inspect the failure and attempt to correct their request.
"""

from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import ClickHouseError

from app.sql_safety import SQLSafetyError, validate_and_rewrite_sql

ALLOWED_DATABASES = {"urbangreen_dw"}


def _validate_database(database: str) -> dict[str, str] | None:
    """
    Validate that a database is available to the read-only tool layer.

    Args:
        database: Name of the ClickHouse database to validate.

    Returns:
        None when the database is allowed, otherwise a model-readable
        dictionary containing an ``error`` message.
    """
    if database in ALLOWED_DATABASES:
        return None

    allowed = ", ".join(sorted(ALLOWED_DATABASES))

    return {"error": (f"Database '{database}' is not allowed. Allowed databases: {allowed}.")}


def list_tables(client: Client, database: str) -> dict:
    """
    List tables in an allowed ClickHouse warehouse database.

    The database name is validated against the configured allow-list before
    querying ``system.tables``. Query parameters are bound rather than
    interpolated into SQL.

    Args:
        client: ClickHouse client used to execute the metadata query.
        database: Name of the warehouse database whose tables should be listed.

    Returns:
        A dictionary containing the database name and table names on success,
        or an ``error`` payload when the database is not allowed or ClickHouse
        rejects the query.
    """
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
    """
    Return column metadata for a table in an allowed warehouse database.

    Metadata is read from ``system.columns`` and includes column names, data
    types, default expressions, and comments. Column comments provide
    additional schema context that can help an LLM understand the meaning of
    fields when generating queries.

    Args:
        client: ClickHouse client used to execute the metadata query.
        database: Name of the warehouse database containing the table.
        table: Name of the table to describe.

    Returns:
        A dictionary containing the database, table, and column metadata on
        success. Returns an ``error`` payload when the database is not allowed,
        the table does not exist, or ClickHouse rejects the query.
    """
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
    """
    Validate, limit, and execute a read-only ClickHouse query.

    SQL is passed through the SQL safety layer before execution. The safety
    layer rejects unsafe statements and injects or clamps result limits. When
    a caller-supplied limit is provided, it acts as a per-query ceiling and is
    itself clamped to ``max_limit``.

    Args:
        client: ClickHouse client used to execute the validated query.
        sql: SQL statement supplied by the caller.
        default_limit: Row limit applied when the query has no explicit limit.
        max_limit: Maximum row limit permitted by the service.
        limit: Optional caller-supplied per-query row limit.

    Returns:
        On success, a dictionary containing the rewritten SQL, applied limit,
        column names, rows, row count, and truncation status. Validation and
        ClickHouse errors are returned as structured ``error`` payloads rather
        than raised to the caller.
    """
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
