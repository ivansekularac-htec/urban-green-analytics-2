import pytest

from app.sql_safety import SQLSafetyError, validate_sql


def test_validate_sql_accepts_select():
    sql = "SELECT * FROM dim_farm"

    result, _ = validate_sql(sql)

    assert result == "SELECT * FROM dim_farm LIMIT 100"


def test_validate_sql_rejects_empty_input():
    with pytest.raises(SQLSafetyError, match="cannot be empty"):
        validate_sql("")


def test_validate_sql_rejects_whitespace_only_input():
    with pytest.raises(SQLSafetyError, match="cannot be empty"):
        validate_sql("   ")


def test_validate_sql_rejects_multiple_statements():
    sql = "SELECT * FROM dim_farm; SELECT * FROM dim_crop"

    with pytest.raises(SQLSafetyError, match="single SQL statement"):
        validate_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "INSERT INTO dim_farm VALUES (1)",
        "UPDATE dim_farm SET name = 'test' WHERE id = 1",
        "DELETE FROM dim_farm WHERE id = 1",
        "CREATE TABLE test (id UInt32)",
        "DROP TABLE dim_farm",
        "ALTER TABLE dim_farm ADD COLUMN test String",
        "TRUNCATE TABLE dim_farm",
        "OPTIMIZE TABLE dim_farm FINAL",
    ],
)
def test_validate_sql_rejects_non_read_only_statements(sql):
    with pytest.raises(SQLSafetyError, match="read-only"):
        validate_sql(sql)


def test_validate_sql_rejects_unparseable_input():
    sql = "SELECT FROM WHERE"

    with pytest.raises(SQLSafetyError, match="Invalid SQL"):
        validate_sql(sql)


def test_validate_sql_accepts_show_tables():
    sql = "SHOW TABLES FROM urbangreen_dw"

    rewritten_sql, limit = validate_sql(sql)

    assert "LIMIT" not in rewritten_sql.upper()
    assert limit == 0


def test_validate_sql_accepts_describe():
    sql = "DESCRIBE dim_farm"

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql
    assert limit == 0


def test_validate_sql_accepts_desc():
    sql = "DESC dim_farm"

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql
    assert limit == 0


def test_validate_sql_accepts_explain():
    sql = "EXPLAIN SELECT * FROM dim_farm"

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql
    assert limit == 0


def test_validate_sql_accepts_clickhouse_specific_select():
    sql = "SELECT * FROM dim_farm FINAL"

    rewritten_sql, limit = validate_sql(sql)

    assert "FINAL" in rewritten_sql
    assert limit == 100


def test_validate_sql_injects_default_limit():
    sql = "SELECT * FROM dim_farm"

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT 100"
    assert limit == 100


def test_validate_sql_keeps_literal_limit_below_maximum():
    sql = "SELECT * FROM dim_farm LIMIT 50"

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT 50"
    assert limit == 50


def test_validate_sql_clamps_literal_limit_above_maximum():
    sql = "SELECT * FROM dim_farm LIMIT 5000"

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql == "SELECT * FROM dim_farm LIMIT 1000"
    assert limit == 1000


def test_validate_sql_injects_limit_on_union():
    sql = """
        SELECT farm_id FROM dim_farm
        UNION ALL
        SELECT farm_id FROM dim_farm
    """

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql.endswith("LIMIT 100")
    assert limit == 100


def test_validate_sql_injects_limit_on_cte():
    sql = """
        WITH latest AS (
            SELECT * FROM fact_daily_farm_metrics
        )
        SELECT * FROM latest
    """

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql.endswith("SELECT * FROM latest LIMIT 100")
    assert "fact_daily_farm_metrics LIMIT 100" not in rewritten_sql
    assert limit == 100


def test_validate_sql_clamps_limit_on_cte():
    sql = """
        WITH latest AS (
            SELECT * FROM fact_daily_farm_metrics
        )
        SELECT * FROM latest
        LIMIT 5000
    """

    rewritten_sql, limit = validate_sql(sql)

    assert rewritten_sql.endswith("SELECT * FROM latest LIMIT 1000")
    assert limit == 1000


def test_validate_sql_preserves_non_literal_limit():
    sql = "SELECT * FROM dim_farm LIMIT (SELECT 50)"

    rewritten_sql, limit = validate_sql(sql)

    assert "LIMIT (SELECT 50)" in rewritten_sql
    assert limit is None
