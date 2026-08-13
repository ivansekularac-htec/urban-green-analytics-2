"""SQL safety layer for queries the model sends us.

Queries are parsed with the ClickHouse dialect, rejected unless they are a
single read-only statement, and rewritten so the result size stays bounded.
The `readonly=2` session already refuses writes server-side; parsing here as
well gives the model a clear error before any round-trip, and lets us clamp
result size, which the server cannot express as nicely.

Error messages are written for the model rather than for a human log reader:
they say what was wrong and what is allowed, so it can correct itself.
"""

import re
from dataclasses import dataclass

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError

from app.config import get_settings

DIALECT = "clickhouse"

# sqlglot falls back to a generic Command node for statements it does not model,
# and that bucket mixes harmless reads with writes: SHOW and EXPLAIN land there,
# but so do OPTIMIZE, ATTACH, RENAME and GRANT. The node type therefore proves
# nothing on its own - only the leading keyword does. If a later sqlglot starts
# modelling SHOW properly, these statements stop arriving as Command; the tests
# pin the behaviour so that change surfaces as a failure rather than as a hole.
READ_ONLY_COMMANDS = frozenset({"SHOW", "DESCRIBE", "DESC", "EXPLAIN"})

ALLOWED_STATEMENTS = "SELECT, SHOW, DESCRIBE, EXPLAIN"

# Returned for SHOW/DESCRIBE/EXPLAIN, where a row limit is meaningless. It means
# "a limit does not apply here", not "no rows".
NO_LIMIT_APPLIED = 0

# A LIMIT we left alone because it is not a literal number returns None instead:
# the query is bounded, we just cannot say by how much before it runs. Keeping
# that apart from 0 stops a caller reading "unknown" as "not applicable". The
# server-side row cap bounds it either way.
UNKNOWN_LIMIT = None


class UnsafeQueryError(ValueError):
    """Raised when a query is not a single read-only statement."""


@dataclass(frozen=True)
class SafeQuery:
    """A query cleared for execution.

    Attributes:
        sql: The normalized, rewritten statement.
        limit: The row limit in effect - the number written into the SQL, 0 when
            a limit does not apply, or None when the query carries a limit we
            cannot read. See NO_LIMIT_APPLIED and UNKNOWN_LIMIT.
    """

    sql: str
    limit: int | None


def prepare_query(
    sql: str,
    *,
    default_limit: int | None = None,
    max_limit: int | None = None,
) -> SafeQuery:
    """Validate, normalize and bound a single read-only statement.

    Args:
        sql: The statement to check.
        default_limit: LIMIT to inject when the query has none. Defaults to the
            configured value.
        max_limit: Ceiling a literal LIMIT is clamped to. Defaults to the
            configured value.

    Returns:
        SafeQuery: The rewritten statement and the limit written into it.

    Raises:
        UnsafeQueryError: If the input is empty, holds more than one statement,
            cannot be parsed, or is not read-only.
    """

    settings = get_settings()
    default_limit = settings.default_row_limit if default_limit is None else default_limit
    max_limit = settings.max_row_limit if max_limit is None else max_limit
    _validate_limits(default_limit=default_limit, max_limit=max_limit)

    statement = _parse_single_statement(sql)
    _reject_inline_settings(statement)

    if isinstance(statement, exp.Describe):
        return SafeQuery(sql=statement.sql(dialect=DIALECT), limit=NO_LIMIT_APPLIED)

    if isinstance(statement, exp.Command):
        keyword = str(statement.this).strip().upper()
        if keyword not in READ_ONLY_COMMANDS:
            raise UnsafeQueryError(
                f"'{keyword}' is not a read-only statement. Allowed: {ALLOWED_STATEMENTS}."
            )
        return SafeQuery(sql=statement.sql(dialect=DIALECT), limit=NO_LIMIT_APPLIED)

    query = _unwrap_query(statement)

    if not isinstance(query, exp.Select | exp.SetOperation):
        raise UnsafeQueryError(
            f"{_statement_name(statement)} is not a read-only statement. "
            f"Allowed: {ALLOWED_STATEMENTS}."
        )

    return _apply_limit(statement, query, default_limit=default_limit, max_limit=max_limit)


def _validate_limits(*, default_limit: int, max_limit: int) -> None:
    """Reject a limit configuration that cannot bound anything."""

    if default_limit < 1:
        raise UnsafeQueryError("The default row limit must be at least 1.")

    if max_limit < 1:
        raise UnsafeQueryError("The maximum row limit must be at least 1.")

    if default_limit > max_limit:
        raise UnsafeQueryError("The default row limit cannot exceed the maximum row limit.")


def _statement_name(expression: exp.Expression) -> str:
    """Turn a node class name into the keyword the model would recognise."""

    return re.sub(r"(?<!^)(?=[A-Z])", " ", type(expression).__name__).upper()


def _parse_single_statement(sql: str) -> exp.Expression:
    """Return the one statement in ``sql``, rejecting anything else."""

    if not sql or not sql.strip():
        raise UnsafeQueryError(
            f"The query is empty. Send one statement. Allowed: {ALLOWED_STATEMENTS}."
        )

    try:
        parsed = sqlglot.parse(sql, read=DIALECT)
    except ParseError as error:
        raise UnsafeQueryError(f"The query is not valid ClickHouse SQL: {error}") from error

    # An input of only whitespace or semicolons parses to a list of None.
    statements = [statement for statement in parsed if statement is not None]

    if not statements:
        raise UnsafeQueryError(
            f"The query is empty. Send one statement. Allowed: {ALLOWED_STATEMENTS}."
        )

    if len(statements) > 1:
        raise UnsafeQueryError(
            f"Only one statement is allowed, but {len(statements)} were sent. "
            "Send them one at a time."
        )

    return statements[0]


def _unwrap_query(statement: exp.Expression) -> exp.Expression:
    """Return the SELECT or set operation that owns the outer LIMIT.

    A CTE parses as a Select carrying the WITH clause, so the limit already
    belongs on that Select. Parentheses are different: ``(SELECT 1)`` arrives
    wrapped in Subquery/Paren, and a limit written onto the wrapper would land
    in the wrong place - or the statement would be rejected as a subquery. With
    is unwrapped too, in case a later parser returns the wrapper instead.
    """

    query = statement

    while isinstance(query, exp.Subquery | exp.Paren | exp.With):
        query = query.this

    return query


def _reject_inline_settings(expression: exp.Expression) -> None:
    """Reject a per-query SETTINGS clause anywhere in the statement.

    ClickHouse lets a query carry its own SETTINGS, which would let the model
    raise the very timeout, memory and row caps this service applies. The clause
    is also legal inside a subquery, so the whole tree is checked, not the root.
    """

    for node in expression.walk():
        if node.args.get("settings"):
            raise UnsafeQueryError(
                "A per-query SETTINGS clause is not allowed. Remove it and send the query again."
            )


def _apply_limit(
    statement: exp.Expression,
    query: exp.Expression,
    *,
    default_limit: int,
    max_limit: int,
) -> SafeQuery:
    """Bound the number of rows the statement can return.

    ``query`` is mutated in place and ``statement`` is what gets rendered, so
    any wrapper the query arrived in survives the rewrite.
    """

    limit = query.args.get("limit")

    if limit is None:
        # On a set operation this wraps the statement in a subquery, which is
        # what we want: a trailing LIMIT would otherwise bind to the last SELECT
        # only, leaving the rest of the union unbounded.
        bounded = query.limit(default_limit)
        rendered = statement if bounded is query else bounded
        return SafeQuery(sql=rendered.sql(dialect=DIALECT), limit=default_limit)

    value = limit.expression

    if not (isinstance(value, exp.Literal) and value.is_int):
        # A placeholder, expression or subquery. Rewriting it would change what
        # the query means, so it stands - the server-side row cap bounds it.
        return SafeQuery(sql=statement.sql(dialect=DIALECT), limit=UNKNOWN_LIMIT)

    requested = int(value.this)

    if requested > max_limit:
        # Replace only the number. Rebuilding the whole LIMIT would discard the
        # ClickHouse `LIMIT n BY col` clause and silently change the result.
        limit.set("expression", exp.Literal.number(max_limit))
        return SafeQuery(sql=statement.sql(dialect=DIALECT), limit=max_limit)

    return SafeQuery(sql=statement.sql(dialect=DIALECT), limit=requested)
