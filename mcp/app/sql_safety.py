"""SQL validation and safety helpers."""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.config import get_settings

READ_ONLY_COMMANDS = {"SHOW", "DESCRIBE", "DESC", "EXPLAIN"}


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

    if not _is_read_only(statement):
        raise SQLSafetyError("Only read-only SQL queries are allowed.")

    if _is_limitless_read_only(statement):
        return statement.sql(dialect="clickhouse"), 0

    settings = get_settings()
    effective_limit = _apply_limit(
        statement,
        default_limit=settings.default_row_limit,
        max_limit=settings.max_row_limit,
    )

    return statement.sql(dialect="clickhouse"), effective_limit


def _is_read_only(statement: exp.Expression) -> bool:
    unwrapped = _unwrap_query(statement)

    if isinstance(unwrapped, (exp.Query, exp.Describe, exp.Show)):
        return True

    return _is_read_only_command(unwrapped)


def _is_read_only_command(statement: exp.Expression) -> bool:
    # SQLGlot may fall back to a generic Command node for valid
    # dialect-specific statements. Inspect Command.this rather than the raw
    # SQL so leading comments and formatting do not affect classification.
    return isinstance(statement, exp.Command) and str(statement.this).upper() in READ_ONLY_COMMANDS


def _is_limitless_read_only(statement: exp.Expression) -> bool:
    return isinstance(statement, (exp.Describe, exp.Show)) or _is_read_only_command(statement)


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
    # Parenthesized queries may be wrapped in Paren/Subquery nodes.
    # Unwrap them before reading or setting LIMIT so the limit applies
    # to the actual SELECT/UNION query.
    query = _unwrap_query(statement)

    if isinstance(query, exp.Query):
        return query

    raise SQLSafetyError("Unable to determine query LIMIT target.")


def _unwrap_query(statement: exp.Expression) -> exp.Expression:
    while isinstance(statement, (exp.Paren, exp.Subquery)):
        statement = statement.this

    return statement
