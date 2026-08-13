"""Tests for the SQL safety layer."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.sql_safety import (
    NO_LIMIT_APPLIED,
    UNKNOWN_LIMIT,
    SafeQuery,
    UnsafeQueryError,
    prepare_query,
)

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


def prepare(sql: str) -> SafeQuery:
    return prepare_query(sql, default_limit=DEFAULT_LIMIT, max_limit=MAX_LIMIT)


# --- rejected input ---------------------------------------------------------


@pytest.mark.parametrize("sql", ["", "   ", "\n\t", ";", ";;"])
def test_empty_input_is_rejected(sql):
    with pytest.raises(UnsafeQueryError, match="empty"):
        prepare(sql)


@pytest.mark.parametrize("sql", ["NOT SQL AT ALL !!!", "SELECT FROM"])
def test_unparseable_input_is_rejected(sql):
    with pytest.raises(UnsafeQueryError, match="not valid ClickHouse SQL"):
        prepare(sql)


def test_multiple_statements_are_rejected():
    with pytest.raises(UnsafeQueryError, match="Only one statement"):
        prepare("SELECT 1; SELECT 2")


def test_trailing_semicolon_is_not_a_second_statement():
    assert prepare("SELECT a FROM t;").sql == "SELECT a FROM t LIMIT 100"


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO t VALUES (1)",
        "UPDATE t SET a = 1",
        "DELETE FROM t",
        "DROP TABLE t",
        "CREATE TABLE t (a Int32)",
        "TRUNCATE TABLE t",
        "ALTER TABLE t DELETE WHERE a = 1",
    ],
)
def test_write_statements_are_rejected(sql):
    with pytest.raises(UnsafeQueryError, match="not a read-only statement"):
        prepare(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "OPTIMIZE TABLE t",
        "ATTACH TABLE t",
        "RENAME TABLE a TO b",
        "GRANT SELECT ON db.* TO u",
    ],
)
def test_write_statements_parsed_as_command_are_rejected(sql):
    """sqlglot parses these as Command, the same node SHOW and EXPLAIN use.

    Allowing the node type would let every one of them through, so the leading
    keyword is what decides.
    """

    with pytest.raises(UnsafeQueryError, match="not a read-only statement"):
        prepare(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT a FROM t SETTINGS max_execution_time = 600",
        "SELECT a FROM t SETTINGS readonly = 0",
        "SELECT a FROM (SELECT 1 SETTINGS max_result_rows = 999999)",
    ],
)
def test_inline_settings_are_rejected(sql):
    """A query may not raise the caps this service applies, at any depth."""

    with pytest.raises(UnsafeQueryError, match="SETTINGS"):
        prepare(sql)


# --- statements that pass without a limit -----------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SHOW TABLES",
        "SHOW TABLES FROM urbangreen_dw",
        "SHOW CREATE TABLE t",
        "DESCRIBE fact_harvests",
        "DESC fact_harvests",
        "EXPLAIN SELECT 1",
    ],
)
def test_read_only_commands_pass_through_without_a_limit(sql):
    result = prepare(sql)

    assert result.limit == NO_LIMIT_APPLIED


# --- limit handling ---------------------------------------------------------


def test_missing_limit_gets_the_default():
    result = prepare("SELECT a FROM t")

    assert result.sql == "SELECT a FROM t LIMIT 100"
    assert result.limit == DEFAULT_LIMIT


def test_limit_below_the_ceiling_is_left_alone():
    result = prepare("SELECT a FROM t LIMIT 50")

    assert result.sql == "SELECT a FROM t LIMIT 50"
    assert result.limit == 50


def test_limit_above_the_ceiling_is_clamped():
    result = prepare("SELECT a FROM t LIMIT 99999")

    assert result.sql == "SELECT a FROM t LIMIT 1000"
    assert result.limit == MAX_LIMIT


def test_limit_at_the_ceiling_is_kept():
    result = prepare("SELECT a FROM t LIMIT 1000")

    assert result.limit == MAX_LIMIT


def test_clamping_keeps_the_offset():
    result = prepare("SELECT a FROM t LIMIT 99999 OFFSET 20")

    assert result.sql == "SELECT a FROM t LIMIT 1000 OFFSET 20"
    assert result.limit == MAX_LIMIT


def test_clamping_keeps_limit_by():
    """`LIMIT n BY col` is top-n per group, not a plain row limit.

    Rebuilding the whole LIMIT would drop the BY clause and quietly return a
    different result set, so only the number is replaced.
    """

    result = prepare("SELECT a FROM t LIMIT 99999 BY farm_id")

    assert result.sql == "SELECT a FROM t LIMIT 1000 BY farm_id"
    assert result.limit == MAX_LIMIT


def test_parenthesized_query_is_accepted():
    result = prepare("(SELECT a FROM t LIMIT 99999)")

    assert "LIMIT 1000" in result.sql
    assert result.limit == MAX_LIMIT


def test_set_operations_other_than_union_are_accepted():
    result = prepare("SELECT 1 EXCEPT SELECT 2")

    assert result.sql.endswith("LIMIT 100")
    assert result.limit == DEFAULT_LIMIT


@pytest.mark.parametrize(
    "sql",
    ["-- list the tables\nSHOW TABLES", "/* list the tables */ SHOW TABLES"],
)
def test_comments_before_the_keyword_do_not_hide_it(sql):
    result = prepare(sql)

    assert result.sql.endswith("SHOW TABLES")
    assert result.limit == NO_LIMIT_APPLIED


@pytest.mark.parametrize(
    ("default_limit", "max_limit", "message"),
    [
        (0, MAX_LIMIT, "default row limit"),
        (-1, MAX_LIMIT, "default row limit"),
        (DEFAULT_LIMIT, 0, "maximum row limit"),
        (2000, MAX_LIMIT, "cannot exceed"),
    ],
)
def test_unusable_limit_configuration_is_rejected(default_limit, max_limit, message):
    with pytest.raises(UnsafeQueryError, match=message):
        prepare_query("SELECT 1", default_limit=default_limit, max_limit=max_limit)


def test_limits_fall_back_to_the_configured_values():
    """Called without overrides, the limits come from settings.

    Every other test passes them explicitly, so without this one the wiring to
    the configuration would be untested.
    """

    settings = SimpleNamespace(default_row_limit=25, max_row_limit=200)

    with patch("app.sql_safety.get_settings", return_value=settings):
        injected = prepare_query("SELECT a FROM t")
        clamped = prepare_query("SELECT a FROM t LIMIT 5000")

    assert injected.sql == "SELECT a FROM t LIMIT 25"
    assert injected.limit == 25
    assert clamped.sql == "SELECT a FROM t LIMIT 200"
    assert clamped.limit == 200


def test_a_non_integer_limit_is_not_read_as_a_number():
    """A float literal must not reach int(), which would raise a bare ValueError
    that callers catching UnsafeQueryError would not see."""

    result = prepare("SELECT a FROM t LIMIT 1.5")

    assert result.limit is UNKNOWN_LIMIT


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT a FROM t LIMIT 1 + 1",
        "SELECT a FROM t LIMIT {n: UInt32}",
        "SELECT a FROM t LIMIT (SELECT 5)",
    ],
)
def test_non_literal_limit_is_left_alone(sql):
    """Rewriting these would change what the query means.

    The limit is reported as unknown rather than 0: the query is bounded by the
    server-side row cap, we just cannot say by how much until it runs.
    """

    result = prepare(sql)

    assert "LIMIT" in result.sql
    assert result.limit is UNKNOWN_LIMIT


def test_cte_gets_the_limit_on_the_inner_select():
    result = prepare("WITH x AS (SELECT 1 AS a) SELECT a FROM x")

    assert result.sql == "WITH x AS (SELECT 1 AS a) SELECT a FROM x LIMIT 100"
    assert result.limit == DEFAULT_LIMIT


def test_cte_limit_above_the_ceiling_is_clamped():
    result = prepare("WITH x AS (SELECT 1 AS a) SELECT a FROM x LIMIT 50000")

    assert result.sql == "WITH x AS (SELECT 1 AS a) SELECT a FROM x LIMIT 1000"
    assert result.limit == MAX_LIMIT


def test_union_is_wrapped_so_the_limit_covers_the_whole_result():
    """A trailing LIMIT would bind to the last SELECT only, so the union is
    wrapped in a subquery and the limit applied outside it."""

    result = prepare("SELECT a FROM t UNION ALL SELECT b FROM u")

    assert result.sql.startswith("SELECT * FROM (")
    assert result.sql.endswith("LIMIT 100")
    assert result.limit == DEFAULT_LIMIT


# --- warehouse syntax must not trip the parser ------------------------------


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT a FROM t FINAL WHERE a > 1",
        "SELECT argMax(value, reading_ts) FROM fact_sensor_readings GROUP BY farm_id",
        "SELECT s FROM t ARRAY JOIN arr AS s",
        "SELECT toYYYYMM(harvest_date) FROM fact_harvests",
    ],
)
def test_clickhouse_specific_syntax_is_accepted(sql):
    result = prepare(sql)

    assert result.sql.endswith("LIMIT 100")
    assert result.limit == DEFAULT_LIMIT
