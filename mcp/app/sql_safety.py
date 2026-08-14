"""
SQL safety utilities for LLM-generated ClickHouse queries.

Validates read-only SQL using sqlglot, rejects unsafe statements,
and injects or clamps LIMIT values before execution.
"""

from __future__ import annotations

import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

DIALECT = "clickhouse"

_META_KEYWORDS = {
    "SHOW",
    "DESCRIBE",
    "DESC",
    "EXPLAIN",
}


class SQLSafetyError(ValueError):
    """
    Error intended to be safe/readable for an LLM caller.

    Example:
        SQL_SAFETY_ERROR[NOT_READ_ONLY]: Only read-only SQL is allowed.
    """

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"SQL_SAFETY_ERROR[{code}]: {message}")


def validate_and_rewrite_sql(
    sql: str,
    *,
    default_limit: int,
    max_limit: int,
) -> tuple[str, int | None]:
    """
    Validate an incoming ClickHouse query and enforce a result LIMIT.

    Returns:
        (normalized_sql, effective_limit)

        effective_limit:
            0     -> SHOW / DESCRIBE / DESC / EXPLAIN
            int   -> literal LIMIT actually present after rewriting
            None  -> non-literal LIMIT; SQL is left unchanged

    Raises:
    SQLSafetyError for:
        - empty SQL
        - invalid/unparseable SQL
        - multiple SQL statements
        - non-read-only statements
        - query-level SETTINGS
        - invalid LIMIT values
    """

    _validate_limit_config(default_limit, max_limit)

    if not isinstance(sql, str) or not sql.strip():
        raise SQLSafetyError(
            "EMPTY",
            "SQL query is empty. Provide exactly one read-only ClickHouse statement.",
        )

    try:
        statements = sqlglot.parse(
            sql,
            read=DIALECT,
        )
    except ParseError as exc:
        raise SQLSafetyError(
            "UNPARSEABLE",
            f"SQL could not be parsed as ClickHouse SQL: {_short_error(exc)}",
        ) from exc
    except Exception as exc:
        # Do not expose an implementation traceback to the model.
        raise SQLSafetyError(
            "UNPARSEABLE",
            f"SQL could not be parsed as ClickHouse SQL: {_short_error(exc)}",
        ) from exc

    statements = [statement for statement in statements if statement is not None]

    if not statements:
        raise SQLSafetyError(
            "EMPTY",
            "SQL query contains no executable statement.",
        )

    if len(statements) != 1:
        raise SQLSafetyError(
            "MULTI_STATEMENT",
            f"Exactly one SQL statement is allowed; received {len(statements)}.",
        )

    statement = statements[0]

    leading_keyword = _leading_keyword(sql)

    # SQLGlot's AST classification for SHOW / DESCRIBE / EXPLAIN has changed
    # between parser versions/dialects. In some cases these statements become
    # a generic Command expression instead of a dedicated AST node.
    #
    # Because of that, after we have already guaranteed that there is exactly
    # one parseable statement, we deliberately use the leading SQL keyword
    # as a compatibility fallback.
    if leading_keyword in _META_KEYWORDS:
        return statement.sql(dialect=DIALECT), 0

    query = _unwrap_query(statement)

    if query is None:
        raise SQLSafetyError(
            "NOT_READ_ONLY",
            (
                "Only read-only SELECT/UNION/CTE queries and "
                "SHOW/DESCRIBE/EXPLAIN statements are allowed; "
                f"received {statement.__class__.__name__}."
            ),
        )

    # Query-level SETTINGS could override service safety limits such as
    # max_result_rows, max_execution_time, or max_memory_usage.
    if any(isinstance(node, exp.Query) and node.args.get("settings") for node in statement.walk()):
        raise SQLSafetyError(
            "SETTINGS_NOT_ALLOWED",
            "Query-level SETTINGS are not allowed.",
        )

    # SELECT ... INTO / INTO OUTFILE-like constructs have a query-shaped
    # root but can introduce a side effect. Keep them outside the LLM path.
    if statement.find(exp.Into):
        raise SQLSafetyError(
            "NOT_READ_ONLY",
            "SELECT ... INTO is not allowed in read-only SQL.",
        )

    effective_limit = _apply_limit(
        query,
        default_limit=default_limit,
        max_limit=max_limit,
    )

    normalized_sql = statement.sql(dialect=DIALECT)

    return normalized_sql, effective_limit


def _unwrap_query(statement: exp.Expression) -> exp.Query | None:
    """
    Return the actual SELECT/UNION/etc. query on which LIMIT belongs.

    Modern SQLGlot represents WITH as the `with_` child of Query.
    Some parser/version shapes may expose an additional wrapper.

    We deliberately unwrap wrappers before reading or changing LIMIT.
    """

    current: exp.Expression | None = statement

    for _ in range(8):
        if current is None:
            return None

        if isinstance(current, exp.Query):
            return current

        # Compatibility for AST shapes which may wrap a query.
        #
        # Do not assume exp.With always has `this`: current SQLGlot normally
        # stores WITH inside Query as the `with_` argument.
        if isinstance(current, exp.With):
            child = current.args.get("this") or current.args.get("expression")

            if isinstance(child, exp.Expression):
                current = child
                continue

            return None

        if isinstance(current, (exp.Subquery, exp.Paren)):
            child = current.args.get("this")

            if isinstance(child, exp.Expression):
                current = child
                continue

        return None

    return None


def _apply_limit(
    query: exp.Query,
    *,
    default_limit: int,
    max_limit: int,
) -> int | None:
    """
    Add/clamp LIMIT on the top-level read query.

    Non-literal LIMIT expressions are intentionally not rewritten.
    """

    limit = query.args.get("limit")

    if limit is None:
        query.limit(
            default_limit,
            dialect=DIALECT,
            copy=False,
        )
        return default_limit

    limit_expression = limit.args.get("expression")

    if not isinstance(limit_expression, exp.Literal):
        # Examples can include query parameters / expressions.
        #
        # We cannot safely determine their runtime value here, so leave them
        # alone. ClickHouse's server-side max_result_rows / timeout remains
        # the final resource boundary.
        return None

    try:
        value = int(str(limit_expression.this))
    except (TypeError, ValueError):
        return None

    if value < 0:
        raise SQLSafetyError(
            "INVALID_LIMIT",
            "LIMIT cannot be negative.",
        )

    if value > max_limit:
        # Change only the LIMIT value instead of replacing the entire Limit
        # node, so dialect-specific LIMIT options survive.
        limit.set(
            "expression",
            exp.Literal.number(max_limit),
        )
        return max_limit

    return value


def _leading_keyword(sql: str) -> str:
    """
    Get the first meaningful SQL keyword while ignoring leading comments.
    """

    remaining = sql.lstrip("\ufeff")

    while True:
        previous = remaining
        remaining = remaining.lstrip()

        # -- comment
        if remaining.startswith("--"):
            newline = remaining.find("\n")
            remaining = "" if newline == -1 else remaining[newline + 1 :]
            continue

        # # comment (supported by various SQL clients)
        if remaining.startswith("#"):
            newline = remaining.find("\n")
            remaining = "" if newline == -1 else remaining[newline + 1 :]
            continue

        # /* block comment */
        if remaining.startswith("/*"):
            end = remaining.find("*/")

            if end == -1:
                return ""

            remaining = remaining[end + 2 :]
            continue

        if remaining == previous:
            break

    match = re.match(r"([A-Za-z]+)", remaining)

    if not match:
        return ""

    return match.group(1).upper()


def _validate_limit_config(
    default_limit: int,
    max_limit: int,
) -> None:
    if default_limit <= 0:
        raise ValueError("default_limit must be greater than zero")

    if max_limit <= 0:
        raise ValueError("max_limit must be greater than zero")

    if default_limit > max_limit:
        raise ValueError("default_limit cannot be greater than max_limit")


def _short_error(exc: Exception) -> str:
    text = " ".join(str(exc).split())

    if len(text) > 500:
        return text[:497] + "..."

    return text
