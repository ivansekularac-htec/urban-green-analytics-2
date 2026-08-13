"""Validation and result-size limiting for LLM-generated ClickHouse SQL."""

import re

import sqlglot
from sqlglot import exp
from sqlglot.errors import ParseError


class SQLSafetyError(ValueError):
    """Raised when SQL is unsafe or cannot be validated."""


_PASSTHROUGH_KEYWORDS = frozenset({"SHOW", "DESCRIBE", "DESC", "EXPLAIN"})

# Skip whitespace and SQL comments before reading the first keyword.
_LEADING_TRIVIA_RE = re.compile(
    r"(?:\s+|--[^\r\n]*(?:\r?\n|$)|/\*.*?\*/)*",
    flags=re.DOTALL,
)
_KEYWORD_RE = re.compile(r"[A-Za-z]+")


def prepare_readonly_sql(
    sql: str,
    default_limit: int,
    max_limit: int,
) -> tuple[str, int | None]:
    """Validate, normalize, and limit one read-only ClickHouse statement.

    Returns:
        A tuple containing normalized SQL and the effective literal LIMIT.

        The returned limit is:
        - 0 for SHOW, DESCRIBE, and EXPLAIN statements;
        - an integer for SELECT, UNION, and CTE queries with a literal limit;
        - None when the query contains a non-literal limit that cannot be
          determined before execution.

    Raises:
        SQLSafetyError: If the input is empty, invalid, contains multiple
            statements, or is not read-only.
    """

    if not isinstance(sql, str) or not sql.strip():
        raise SQLSafetyError("SQL input is empty. Provide one read-only statement.")

    _validate_limit_configuration(default_limit, max_limit)

    try:
        parsed = sqlglot.parse(sql, dialect="clickhouse")
    except ParseError as exc:
        raise SQLSafetyError(f"SQL could not be parsed as ClickHouse SQL: {exc}") from exc

    statements = [statement for statement in parsed if statement is not None]

    if not statements:
        raise SQLSafetyError("SQL could not be parsed. Provide one valid read-only statement.")

    if len(statements) != 1:
        raise SQLSafetyError(f"SQL must contain exactly one statement; received {len(statements)}.")

    statement = statements[0]
    leading_keyword = _leading_keyword(sql)

    # sqlglot sometimes represents ClickHouse SHOW/DESCRIBE/EXPLAIN as a
    # generic Command node, and that behaviour can change between parser
    # versions. Check the leading keyword instead of allowing every Command:
    # OPTIMIZE, for example, can also be parsed as Command and must stay blocked.
    if leading_keyword in _PASSTHROUGH_KEYWORDS:
        return statement.sql(dialect="clickhouse"), 0

    query = _unwrap_query(statement)

    if not isinstance(query, (exp.Select, exp.Union)):
        statement_name = leading_keyword or type(statement).__name__.upper()
        raise SQLSafetyError(
            "Only read-only SELECT, UNION, CTE, SHOW, DESCRIBE, and EXPLAIN "
            f"statements are allowed; received {statement_name}."
        )

    limit = query.args.get("limit")

    if limit is None:
        query.set(
            "limit",
            exp.Limit(expression=exp.Literal.number(default_limit)),
        )
        return statement.sql(dialect="clickhouse"), default_limit

    limit_expression = limit.expression
    literal_limit = _literal_integer(limit_expression)

    if literal_limit is None:
        # Parameters and expressions cannot be evaluated safely here. Leave
        # them unchanged; ClickHouse's server-side caps still bound execution.
        return statement.sql(dialect="clickhouse"), None

    effective_limit = min(literal_limit, max_limit)

    if effective_limit != literal_limit:
        # Replace only the numeric expression so OFFSET and LIMIT ... BY
        # metadata remain intact.
        limit.set("expression", exp.Literal.number(effective_limit))

    return statement.sql(dialect="clickhouse"), effective_limit


def _validate_limit_configuration(default_limit: int, max_limit: int) -> None:
    if default_limit < 0:
        raise SQLSafetyError("The default row limit cannot be negative.")

    if max_limit < 0:
        raise SQLSafetyError("The maximum row limit cannot be negative.")

    if default_limit > max_limit:
        raise SQLSafetyError("The default row limit cannot exceed the maximum row limit.")


def _leading_keyword(sql: str) -> str:
    trivia = _LEADING_TRIVIA_RE.match(sql)
    start = trivia.end() if trivia else 0
    keyword = _KEYWORD_RE.match(sql, start)

    return keyword.group(0).upper() if keyword else ""


def _unwrap_query(statement: exp.Expression) -> exp.Expression:
    """Return the SELECT/UNION that owns the outer result LIMIT.

    In the current sqlglot ClickHouse AST, a WITH clause is attached to its
    SELECT or UNION through the ``with_`` argument. Parenthesized queries can
    additionally introduce Subquery/Paren wrappers, so LIMIT must be read from
    and written to the contained query rather than to those wrappers.
    """

    query = statement

    while isinstance(query, (exp.Subquery, exp.Paren)):
        query = query.this

    return query


def _literal_integer(expression: exp.Expression | None) -> int | None:
    if not isinstance(expression, exp.Literal):
        return None

    if expression.is_string:
        return None

    try:
        return int(expression.this)
    except (TypeError, ValueError):
        return None
