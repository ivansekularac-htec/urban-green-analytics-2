"""SQL validation and safety helpers."""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.config import get_settings


class SQLSafetyError(ValueError):
    """Raised when SQL does not satisfy the MCP safety rules."""


def validate_sql(sql: str) -> tuple[str, int | None]:
    """Validate, normalize, and bound a single read-only SQL statement."""

    if not sql.strip():
        raise SQLSafetyError("SQL query cannot be empty.")

    try:
        statements = sqlglot.parse(sql, dialect="clickhouse")
    except ParseError as exc:
        raise SQLSafetyError(f"Invalid SQL query: {exc}") from exc

    if len(statements) != 1:
        raise SQLSafetyError("Only a single SQL statement is allowed.")

    statement = statements[0]

    if not _is_read_only(statement, sql):
        raise SQLSafetyError("Only read-only SQL queries are allowed.")

    if _has_read_only_command_prefix(sql):
        return statement.sql(dialect="clickhouse"), 0

    settings = get_settings()
    effective_limit = _apply_limit(
        statement,
        default_limit=settings.default_row_limit,
        max_limit=settings.max_row_limit,
    )

    return statement.sql(dialect="clickhouse"), effective_limit


def _is_read_only(statement: exp.Expression, original_sql: str) -> bool:
    if isinstance(statement, exp.Query):
        return True

    return _has_read_only_command_prefix(original_sql)


def _has_read_only_command_prefix(sql: str) -> bool:
    # SQLGlot may represent valid SHOW/DESCRIBE/EXPLAIN statements differently
    # across versions, including falling back to a generic Command node.
    # Keep this leading-keyword fallback so these known read-only statements
    # remain accepted even if their AST representation changes.
    first_keyword = sql.lstrip().split(maxsplit=1)[0].upper()

    return first_keyword in {"SHOW", "DESCRIBE", "DESC", "EXPLAIN"}


def _apply_limit(
    statement: exp.Expression,
    default_limit: int,
    max_limit: int,
) -> int | None:
    query = _limit_target(statement)

    limit = query.args.get("limit")

    if limit is None:
        query.limit(default_limit, copy=False)
        return default_limit

    limit_expression = limit.expression

    if not isinstance(limit_expression, exp.Literal) or not limit_expression.is_int:
        return None

    requested_limit = int(limit_expression.this)
    effective_limit = min(requested_limit, max_limit)

    if requested_limit > max_limit:
        query.limit(max_limit, copy=False)

    return effective_limit


def _limit_target(statement: exp.Expression) -> exp.Query:
    # In SQLGlot 30.13, a WITH clause is attached to the SELECT/UNION query
    # through its `with_` argument rather than wrapping the query. Therefore
    # the root Query is already the correct node for reading or setting LIMIT.
    if isinstance(statement, exp.Query):
        return statement

    raise SQLSafetyError("Unable to determine query LIMIT target.")
