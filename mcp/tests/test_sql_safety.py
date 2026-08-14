"""
Unit tests for the SQL safety layer.

Covers read-only validation, SQL parsing, LIMIT injection and clamping,
CTEs, UNIONs, and SHOW/DESCRIBE/EXPLAIN pass-through behavior.
"""

import pytest

from app.sql_safety import (
    SQLSafetyError,
    validate_and_rewrite_sql,
)

DEFAULT = 100
MAX = 500


def safe(sql: str):
    """Validate SQL using the test LIMIT configuration."""
    return validate_and_rewrite_sql(
        sql,
        default_limit=DEFAULT,
        max_limit=MAX,
    )


@pytest.mark.parametrize(
    "sql",
    [
        "",
        "   ",
        "\n\t",
    ],
)
def test_empty_sql_rejected(sql):
    """Reject empty or whitespace-only SQL."""
    with pytest.raises(SQLSafetyError, match=r"\[EMPTY\]"):
        safe(sql)


def test_unparseable_sql_rejected():
    """Reject malformed SQL."""
    with pytest.raises(SQLSafetyError, match=r"\[UNPARSEABLE\]"):
        safe("SELECT (")


def test_multiple_statements_rejected():
    """Reject multiple SQL statements."""
    with pytest.raises(SQLSafetyError, match=r"\[MULTI_STATEMENT\]"):
        safe("SELECT 1; SELECT 2")


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO foo VALUES (1)",
        "UPDATE foo SET x = 1",
        "DELETE FROM foo WHERE x = 1",
        "CREATE TABLE foo (x UInt32) ENGINE = Memory",
        "DROP TABLE foo",
        "ALTER TABLE foo ADD COLUMN y UInt32",
        "TRUNCATE TABLE foo",
        "OPTIMIZE TABLE foo FINAL",
    ],
)
def test_write_shaped_statements_rejected(sql):
    """Reject non-read-only SQL statements."""
    with pytest.raises(SQLSafetyError):
        safe(sql)


def test_default_limit_is_added():
    """Add the default LIMIT when none is provided."""
    rewritten, limit = safe(
        """
        SELECT farm_id, crop_id
        FROM urbangreen_dw.fact_harvests
        """
    )

    assert limit == DEFAULT
    assert rewritten.endswith(f"LIMIT {DEFAULT}")


def test_existing_limit_is_preserved():
    """Preserve an existing LIMIT below the ceiling."""
    rewritten, limit = safe(
        """
        SELECT *
        FROM urbangreen_dw.fact_harvests
        LIMIT 25
        """
    )

    assert limit == 25
    assert rewritten.endswith("LIMIT 25")


def test_limit_above_ceiling_is_clamped():
    """Clamp LIMIT values above the configured maximum."""
    rewritten, limit = safe(
        """
        SELECT *
        FROM urbangreen_dw.fact_harvests
        LIMIT 10000
        """
    )

    assert limit == MAX
    assert rewritten.endswith(f"LIMIT {MAX}")
    assert "10000" not in rewritten


def test_cte_gets_limit_on_main_query():
    """Apply LIMIT to the main CTE query."""
    rewritten, limit = safe(
        """
        WITH recent AS (
            SELECT *
            FROM urbangreen_dw.fact_harvests
            WHERE harvest_date >= today() - 7
        )
        SELECT *
        FROM recent
        """
    )

    assert limit == DEFAULT

    # LIMIT must apply to the query using the CTE,
    # not to the CTE definition.
    assert rewritten.endswith(f"LIMIT {DEFAULT}")

    assert f"today() - 7 LIMIT {DEFAULT}" not in rewritten


def test_union_gets_default_limit():
    """Apply the default LIMIT to UNION queries."""
    rewritten, limit = safe(
        """
        SELECT farm_id
        FROM urbangreen_dw.fact_harvests

        UNION ALL

        SELECT farm_id
        FROM urbangreen_dw.fact_daily_farm_metrics
        """
    )

    assert limit == DEFAULT
    assert rewritten.endswith(f"LIMIT {DEFAULT}")


def test_show_tables_passes_without_limit():
    """Allow SHOW TABLES without adding a LIMIT."""
    rewritten, limit = safe("SHOW TABLES FROM urbangreen_dw")

    assert limit == 0
    assert "LIMIT" not in rewritten.upper()


def test_describe_passes_without_limit():
    """Allow DESCRIBE without adding a LIMIT."""
    rewritten, limit = safe("DESCRIBE urbangreen_dw.fact_harvests")

    assert limit == 0
    assert "LIMIT" not in rewritten.upper()


def test_desc_passes_without_limit():
    """Allow DESC without adding a LIMIT."""
    rewritten, limit = safe("DESC urbangreen_dw.fact_harvests")

    assert limit == 0
    assert "LIMIT" not in rewritten.upper()


def test_explain_passes_without_limit():
    """Allow EXPLAIN without adding a LIMIT."""
    rewritten, limit = safe(
        """
        EXPLAIN
        SELECT *
        FROM urbangreen_dw.fact_harvests
        """
    )

    assert limit == 0


def test_leading_comment_before_show_is_supported():
    """Allow SHOW statements preceded by comments."""
    rewritten, limit = safe(
        """
        -- LLM wants schema information
        SHOW TABLES FROM urbangreen_dw
        """
    )

    assert limit == 0


def test_clickhouse_final_syntax_is_accepted():
    """Accept ClickHouse FINAL syntax."""
    rewritten, limit = safe(
        """
        SELECT farm_id
        FROM urbangreen_dw.fact_harvests FINAL
        """
    )

    assert limit == DEFAULT
    assert "FINAL" in rewritten


def test_clickhouse_argmax_is_accepted():
    """Accept ClickHouse argMax function syntax."""
    rewritten, limit = safe(
        """
        SELECT
            farm_id,
            argMax(status, recorded_at)
        FROM urbangreen_dw.fact_daily_farm_metrics
        GROUP BY farm_id
        """
    )

    assert limit == DEFAULT
    assert "argMax" in rewritten or "ARG_MAX" in rewritten.upper()


def test_select_into_is_rejected():
    """Reject SELECT INTO statements."""
    with pytest.raises(
        SQLSafetyError,
        match=r"\[NOT_READ_ONLY\]",
    ):
        safe(
            """
            SELECT *
            INTO result
            FROM urbangreen_dw.fact_harvests
            """
        )


def test_valid_select_followed_by_drop_is_rejected():
    """Reject a valid SELECT followed by a write statement."""
    with pytest.raises(
        SQLSafetyError,
        match=r"\[MULTI_STATEMENT\]",
    ):
        safe(
            """
            SELECT *
            FROM urbangreen_dw.fact_harvests;

            DROP TABLE urbangreen_dw.fact_harvests;
            """
        )


def test_invalid_limit_configuration():
    """Reject an invalid LIMIT configuration."""
    with pytest.raises(ValueError):
        validate_and_rewrite_sql(
            "SELECT 1",
            default_limit=1000,
            max_limit=100,
        )


def test_non_literal_limit_is_preserved():
    """Preserve a non-literal LIMIT expression."""
    rewritten, limit = safe(
        """
        SELECT *
        FROM urbangreen_dw.fact_harvests
        LIMIT {row_limit:UInt32}
        """
    )

    assert limit is None
    assert "row_limit" in rewritten
    assert "UInt32" in rewritten


@pytest.mark.parametrize(
    "setting",
    [
        "max_result_rows = 0",
        "max_execution_time = 0",
        "max_memory_usage = 0",
    ],
)
def test_query_level_settings_are_rejected(setting):
    """Reject query-level SETTINGS that could override safety limits."""
    with pytest.raises(
        SQLSafetyError,
        match=r"\[SETTINGS_NOT_ALLOWED\]",
    ):
        safe(
            f"""
            SELECT *
            FROM urbangreen_dw.fact_harvests
            SETTINGS {setting}
            """
        )
