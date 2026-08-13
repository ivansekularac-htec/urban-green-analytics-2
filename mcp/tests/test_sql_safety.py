from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.sql_safety import SQLSafetyError, validate_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM dim_farm FINAL",
        "SELECT argMax(name, _version) FROM dim_farm",
        "SELECT * FROM dim_farm ARRAY JOIN some_array",
    ],
)
def test_clickhouse_specific_syntax_is_allowed(sql):
    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql.endswith("LIMIT 100")
    assert limit == 100


def test_empty_sql_is_rejected():
    with pytest.raises(SQLSafetyError, match="cannot be empty"):
        validate_sql("   ")


@pytest.mark.parametrize(
    "sql",
    [
        "-- list all tables\nSHOW TABLES FROM urbangreen_dw",
        "-- explain the query\nEXPLAIN SELECT * FROM dim_farm",
    ],
)
def test_metadata_commands_allow_leading_comments(sql):
    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql
    assert limit == 0


def test_multiple_statements_are_rejected():
    with pytest.raises(SQLSafetyError, match="single SQL statement"):
        validate_sql("SELECT 1; SELECT 2")


def test_unparseable_sql_is_rejected():
    with pytest.raises(SQLSafetyError, match="Invalid SQL"):
        validate_sql("SELECT FROM WHERE")


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO dim_farm VALUES (1)",
        "DELETE FROM dim_farm",
        "DROP TABLE dim_farm",
        "TRUNCATE TABLE dim_farm",
        "OPTIMIZE TABLE dim_farm",
    ],
)
def test_write_statements_are_rejected(sql):
    with pytest.raises(SQLSafetyError, match="read-only"):
        validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "SHOW TABLES FROM urbangreen_dw",
        "DESCRIBE dim_farm",
        "EXPLAIN SELECT * FROM dim_farm",
    ],
)
def test_metadata_statements_are_allowed(sql):
    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql
    assert limit == 0


def test_row_limits_come_from_settings():
    settings = SimpleNamespace(
        default_row_limit=25,
        max_row_limit=200,
    )

    with patch("app.sql_safety.get_settings", return_value=settings):
        default_sql, default_limit = validate_sql("SELECT * FROM dim_farm")
        clamped_sql, clamped_limit = validate_sql("SELECT * FROM dim_farm LIMIT 5000")

    assert default_sql == "SELECT * FROM dim_farm LIMIT 25"
    assert default_limit == 25
    assert clamped_sql == "SELECT * FROM dim_farm LIMIT 200"
    assert clamped_limit == 200


def test_default_limit_is_injected():
    rewritten_sql, limit = validate_sql("SELECT * FROM dim_farm")

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT 100"
    assert limit == 100


def test_literal_limit_below_ceiling_is_preserved():
    rewritten_sql, limit = validate_sql("SELECT * FROM dim_farm LIMIT 50")

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT 50"
    assert limit == 50


def test_literal_limit_above_ceiling_is_clamped():
    rewritten_sql, limit = validate_sql("SELECT * FROM dim_farm LIMIT 5000")

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT 1000"
    assert limit == 1000


def test_default_limit_is_applied_to_union_result():
    rewritten_sql, limit = validate_sql("SELECT * FROM a UNION ALL SELECT * FROM b")

    assert rewritten_sql.endswith("LIMIT 100")
    assert limit == 100


def test_default_limit_is_applied_to_outer_cte_query():
    rewritten_sql, limit = validate_sql(
        "WITH farms AS (SELECT * FROM dim_farm) SELECT * FROM farms"
    )

    assert rewritten_sql == ("WITH farms AS (SELECT * FROM dim_farm) SELECT * FROM farms LIMIT 100")
    assert limit == 100


def test_non_literal_limit_is_preserved():
    rewritten_sql, limit = validate_sql("SELECT * FROM dim_farm LIMIT {rows:UInt64}")

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT {rows: UInt64}"
    assert limit is None


def test_limit_clamp_preserves_offset():
    rewritten_sql, limit = validate_sql("SELECT * FROM dim_farm LIMIT 5000 OFFSET 5")

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT 1000 OFFSET 5"
    assert limit == 1000


def test_negative_limit_is_rejected():
    with pytest.raises(SQLSafetyError, match="LIMIT cannot be negative"):
        validate_sql("SELECT * FROM dim_farm LIMIT -5")
