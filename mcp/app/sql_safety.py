"""SQL safety utilities for validating and limiting read-only ClickHouse queries."""

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.config import get_settings

_SAFE_COMMANDS = {"SHOW", "DESCRIBE", "EXPLAIN"}


class SQLSafetyError(ValueError):
    """Raised when SQL is rejected by the safety layer."""


def validate_sql(sql: str) -> tuple[str, int | None]:
    """Validate, normalize, and apply row limits to a single read-only SQL statement."""
    statement = _parse_single_statement(sql)

    if _is_metadata_statement(statement, sql):
        return statement.sql(dialect="clickhouse"), 0

    if not isinstance(statement, (exp.Select, exp.Union)):
        raise SQLSafetyError("Only read-only SQL statements are allowed.")

    settings = get_settings()

    return _apply_limit(
        statement,
        default_limit=settings.default_row_limit,
        max_limit=settings.max_row_limit,
    )


def _parse_single_statement(sql: str) -> exp.Expression:
    """Parse one ClickHouse SQL statement and reject empty, invalid, or multi-statement input."""
    if not sql or not sql.strip():
        raise SQLSafetyError("SQL query cannot be empty.")

    try:
        statements = [
            statement
            for statement in sqlglot.parse(sql, dialect="clickhouse")
            if statement is not None
        ]
    except ParseError as exc:
        raise SQLSafetyError(f"Invalid SQL: {exc}") from exc

    if len(statements) != 1:
        raise SQLSafetyError("Only a single SQL statement is allowed.")

    return statements[0]


def _is_metadata_statement(statement: exp.Expression, sql: str) -> bool:
    """Return whether the statement is an allowed read-only metadata command."""
    if isinstance(statement, exp.Describe):
        return True

    if isinstance(statement, exp.Command):
        # SQLGlot may fall back to Command for valid ClickHouse statements
        # such as SHOW and EXPLAIN, so preserve a leading-keyword fallback.
        keyword = sql.lstrip().split(None, 1)[0].upper()
        return keyword in _SAFE_COMMANDS

    return False


def _apply_limit(
    statement: exp.Select | exp.Union,
    default_limit: int,
    max_limit: int,
) -> tuple[str, int | None]:
    """Inject, preserve, or clamp the outer query LIMIT and return its effective value."""
    limit = statement.args.get("limit")

    if limit is None:
        statement = statement.limit(default_limit)
        return statement.sql(dialect="clickhouse"), default_limit

    limit_expression = limit.expression

    if not isinstance(limit_expression, exp.Literal) or limit_expression.is_string:
        return statement.sql(dialect="clickhouse"), None

    literal_limit = int(limit_expression.this)
    effective_limit = min(literal_limit, max_limit)

    if literal_limit > max_limit:
        statement = statement.limit(max_limit)

    return statement.sql(dialect="clickhouse"), effective_limit
