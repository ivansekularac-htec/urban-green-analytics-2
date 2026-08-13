"""Tests for ClickHouse SQL validation and result-size limiting."""

import pytest
import sqlglot
from sqlglot import exp

from app.sql_safety import SQLSafetyError, prepare_readonly_sql

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000


def prepare(sql: str) -> tuple[str, int | None]:
    return prepare_readonly_sql(
        sql,
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
    )


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO events VALUES (1)",
        "UPDATE events SET value = 1",
        "DELETE FROM events WHERE id = 1",
        "CREATE TABLE unsafe_table (id Int32) ENGINE = Memory",
        "ALTER TABLE events ADD COLUMN unsafe_column String",
        "DROP TABLE events",
        "TRUNCATE TABLE events",
        "OPTIMIZE TABLE events FINAL",
    ],
)
def test_rejects_non_read_only_statements(sql):
    with pytest.raises(SQLSafetyError, match="Only read-only"):
        prepare(sql)


@pytest.mark.parametrize("sql", ["", " ", "\n\t"])
def test_rejects_empty_input(sql):
    with pytest.raises(SQLSafetyError, match="SQL input is empty"):
        prepare(sql)


def test_rejects_unparseable_input():
    with pytest.raises(SQLSafetyError, match="could not be parsed"):
        prepare("SELECT * FROM")


def test_rejects_multiple_statements():
    with pytest.raises(SQLSafetyError, match="exactly one statement"):
        prepare("SELECT 1; SELECT 2")


def test_adds_default_limit_to_select():
    rewritten_sql, effective_limit = prepare("select * from events")

    assert rewritten_sql == "SELECT * FROM events LIMIT 100"
    assert effective_limit == DEFAULT_LIMIT


def test_preserves_literal_limit_below_ceiling():
    rewritten_sql, effective_limit = prepare("SELECT * FROM events LIMIT 25")

    assert rewritten_sql == "SELECT * FROM events LIMIT 25"
    assert effective_limit == 25


def test_clamps_literal_limit_above_ceiling():
    rewritten_sql, effective_limit = prepare("SELECT * FROM events LIMIT 5000")

    assert rewritten_sql == "SELECT * FROM events LIMIT 1000"
    assert effective_limit == MAX_LIMIT


def test_preserves_offset_when_clamping_limit():
    rewritten_sql, effective_limit = prepare("SELECT * FROM events LIMIT 5000 OFFSET 20")

    assert rewritten_sql == "SELECT * FROM events LIMIT 1000 OFFSET 20"
    assert effective_limit == MAX_LIMIT


def test_preserves_limit_by_when_clamping():
    rewritten_sql, effective_limit = prepare("SELECT * FROM events LIMIT 5000 BY farm_id")

    assert rewritten_sql == "SELECT * FROM events LIMIT 1000 BY farm_id"
    assert effective_limit == MAX_LIMIT


def test_leaves_non_literal_limit_unchanged():
    rewritten_sql, effective_limit = prepare("SELECT * FROM events LIMIT {row_limit:Int32}")

    assert rewritten_sql == ("SELECT * FROM events LIMIT {row_limit: Int32}")
    assert effective_limit is None


def test_adds_limit_to_outer_select_of_cte():
    rewritten_sql, effective_limit = prepare(
        """
        WITH recent AS (
            SELECT * FROM events
        )
        SELECT * FROM recent
        """
    )

    assert rewritten_sql == ("WITH recent AS (SELECT * FROM events) SELECT * FROM recent LIMIT 100")
    assert effective_limit == DEFAULT_LIMIT


def test_preserves_limit_inside_cte_and_limits_outer_result():
    rewritten_sql, effective_limit = prepare(
        """
        WITH recent AS (
            SELECT * FROM events LIMIT 10
        )
        SELECT * FROM recent
        """
    )

    assert rewritten_sql == (
        "WITH recent AS (SELECT * FROM events LIMIT 10) SELECT * FROM recent LIMIT 100"
    )
    assert effective_limit == DEFAULT_LIMIT


def test_limits_complete_union_result():
    rewritten_sql, effective_limit = prepare("SELECT 1 UNION ALL SELECT 2")

    parsed = sqlglot.parse_one(rewritten_sql, dialect="clickhouse")

    assert isinstance(parsed, exp.Select)
    assert isinstance(parsed.args["from_"].this.this, exp.Union)
    assert parsed.args["limit"].expression.this == str(DEFAULT_LIMIT)
    assert effective_limit == DEFAULT_LIMIT


@pytest.mark.parametrize(
    ("sql", "expected_sql"),
    [
        (
            "SHOW TABLES FROM urbangreen_dw",
            "SHOW TABLES FROM urbangreen_dw",
        ),
        (
            "DESCRIBE events",
            "DESCRIBE events",
        ),
        (
            "EXPLAIN SELECT * FROM events",
            "EXPLAIN SELECT * FROM events",
        ),
    ],
)
def test_metadata_statements_pass_through_without_limit(sql, expected_sql):
    rewritten_sql, effective_limit = prepare(sql)

    assert rewritten_sql == expected_sql
    assert effective_limit == 0


def test_command_fallback_does_not_allow_optimize():
    with pytest.raises(SQLSafetyError, match="OPTIMIZE"):
        prepare("OPTIMIZE TABLE events FINAL")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM events FINAL",
        "SELECT argMax(value, observed_at) FROM events",
        "SELECT * FROM events ARRAY JOIN tags",
    ],
)
def test_accepts_clickhouse_specific_select_syntax(sql):
    rewritten_sql, effective_limit = prepare(sql)

    assert rewritten_sql.endswith("LIMIT 100")
    assert effective_limit == DEFAULT_LIMIT


def test_accepts_comments_before_metadata_keyword():
    rewritten_sql, effective_limit = prepare("-- inspect available tables\nSHOW TABLES")

    assert rewritten_sql.endswith("SHOW TABLES")
    assert effective_limit == 0


@pytest.mark.parametrize(
    ("default_limit", "max_limit", "message"),
    [
        (-1, 1000, "default row limit"),
        (100, -1, "maximum row limit"),
        (1001, 1000, "cannot exceed"),
    ],
)
def test_rejects_invalid_limit_configuration(
    default_limit,
    max_limit,
    message,
):
    with pytest.raises(SQLSafetyError, match=message):
        prepare_readonly_sql(
            "SELECT 1",
            default_limit=default_limit,
            max_limit=max_limit,
        )
