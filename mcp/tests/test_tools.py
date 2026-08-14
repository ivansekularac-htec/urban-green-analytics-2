"""
Unit tests for the core ClickHouse tools.

Covers table discovery, schema metadata retrieval, SQL safety integration,
query execution, result limits, truncation detection, and structured
error handling.
"""

from unittest.mock import MagicMock

from clickhouse_connect.driver.exceptions import DatabaseError

from app.tools import describe_table, execute_query, list_tables

DEFAULT_LIMIT = 100
MAX_LIMIT = 1000

# ---------------------------------------------------------------------------
# list_tables
# ---------------------------------------------------------------------------


def test_list_tables_returns_tables():
    client = MagicMock()
    result = MagicMock()
    result.result_rows = [
        ("dim_farm",),
        ("fact_daily_farm_metrics",),
        ("fact_harvests",),
    ]
    client.query.return_value = result

    response = list_tables(client, "urbangreen_dw")

    assert response == {
        "database": "urbangreen_dw",
        "tables": [
            "dim_farm",
            "fact_daily_farm_metrics",
            "fact_harvests",
        ],
    }


def test_list_tables_rejects_disallowed_database():
    client = MagicMock()

    response = list_tables(client, "system")

    assert response == {
        "error": ("Database 'system' is not allowed. Allowed databases: urbangreen_dw.")
    }

    client.query.assert_not_called()


def test_list_tables_uses_bound_database_parameter():
    client = MagicMock()
    result = MagicMock()
    result.result_rows = []
    client.query.return_value = result

    list_tables(client, "urbangreen_dw")

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in sql
    assert parameters == {"database": "urbangreen_dw"}
    assert "urbangreen_dw" not in sql


def test_list_tables_returns_clickhouse_error():
    client = MagicMock()
    client.query.side_effect = DatabaseError("Query failed")

    response = list_tables(client, "urbangreen_dw")

    assert response == {
        "error": "ClickHouse error: Query failed",
    }


# ---------------------------------------------------------------------------
# describe_table
# ---------------------------------------------------------------------------


def test_describe_table_returns_columns():
    client = MagicMock()
    result = MagicMock()
    result.result_rows = [
        (
            "farm_id",
            "UInt32",
            "",
            "",
            "Unique identifier of the farm.",
        ),
        (
            "farm_name",
            "String",
            "",
            "",
            "Human-readable farm name.",
        ),
        (
            "created_at",
            "DateTime",
            "DEFAULT",
            "now()",
            "Timestamp when the farm was created.",
        ),
    ]
    client.query.return_value = result

    response = describe_table(
        client,
        "urbangreen_dw",
        "dim_farm",
    )

    assert response == {
        "database": "urbangreen_dw",
        "table": "dim_farm",
        "columns": [
            {
                "name": "farm_id",
                "type": "UInt32",
                "default_kind": "",
                "default_expression": "",
                "comment": "Unique identifier of the farm.",
            },
            {
                "name": "farm_name",
                "type": "String",
                "default_kind": "",
                "default_expression": "",
                "comment": "Human-readable farm name.",
            },
            {
                "name": "created_at",
                "type": "DateTime",
                "default_kind": "DEFAULT",
                "default_expression": "now()",
                "comment": "Timestamp when the farm was created.",
            },
        ],
    }


def test_describe_table_rejects_disallowed_database():
    client = MagicMock()

    response = describe_table(
        client,
        "system",
        "tables",
    )

    assert response == {
        "error": ("Database 'system' is not allowed. Allowed databases: urbangreen_dw.")
    }

    client.query.assert_not_called()


def test_describe_table_returns_error_for_unknown_table():
    client = MagicMock()
    result = MagicMock()
    result.result_rows = []
    client.query.return_value = result

    response = describe_table(
        client,
        "urbangreen_dw",
        "missing_table",
    )

    assert response == {
        "error": "Table 'urbangreen_dw.missing_table' was not found.",
    }


def test_describe_table_uses_bound_parameters():
    client = MagicMock()
    result = MagicMock()
    result.result_rows = [
        ("farm_id", "UInt32", "", "", "Farm identifier"),
    ]
    client.query.return_value = result

    describe_table(
        client,
        "urbangreen_dw",
        "dim_farm",
    )

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in sql
    assert "{table:String}" in sql

    assert parameters == {
        "database": "urbangreen_dw",
        "table": "dim_farm",
    }

    assert "urbangreen_dw" not in sql
    assert "dim_farm" not in sql


def test_describe_table_returns_clickhouse_error():
    client = MagicMock()
    client.query.side_effect = DatabaseError("Query failed")

    response = describe_table(
        client,
        "urbangreen_dw",
        "dim_farm",
    )

    assert response == {
        "error": "ClickHouse error: Query failed",
    }


# ---------------------------------------------------------------------------
# execute_query
# ---------------------------------------------------------------------------


def test_execute_query_returns_result():
    client = MagicMock()
    result = MagicMock()
    result.column_names = ("farm_id", "farm_name")
    result.result_rows = [
        (1, "Farm One"),
        (2, "Farm Two"),
    ]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id, farm_name FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
    )

    assert response == {
        "sql": (f"SELECT farm_id, farm_name FROM urbangreen_dw.dim_farm LIMIT {DEFAULT_LIMIT}"),
        "limit": DEFAULT_LIMIT,
        "columns": ["farm_id", "farm_name"],
        "rows": [
            (1, "Farm One"),
            (2, "Farm Two"),
        ],
        "row_count": 2,
        "truncated": False,
    }

    client.query.assert_called_once_with(response["sql"])


def test_execute_query_applies_caller_limit():
    client = MagicMock()
    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [(1,), (2,)]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
        limit=25,
    )

    assert response["limit"] == 25
    assert response["sql"].endswith("LIMIT 25")


def test_execute_query_clamps_caller_limit_to_ceiling():
    client = MagicMock()
    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [(1,)]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
        limit=5000,
    )

    assert response["limit"] == MAX_LIMIT
    assert response["sql"].endswith(f"LIMIT {MAX_LIMIT}")


def test_execute_query_preserves_smaller_sql_limit():
    client = MagicMock()
    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [(1,)]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM urbangreen_dw.dim_farm LIMIT 10",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
        limit=50,
    )

    assert response["limit"] == 10
    assert response["sql"].endswith("LIMIT 10")


def test_execute_query_returns_sql_safety_error():
    client = MagicMock()

    response = execute_query(
        client,
        "DELETE FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
    )

    assert "error" in response
    assert "SQL_SAFETY_ERROR" in response["error"]

    client.query.assert_not_called()


def test_execute_query_returns_clickhouse_error():
    client = MagicMock()
    client.query.side_effect = DatabaseError("Unknown identifier farm_namee")

    response = execute_query(
        client,
        "SELECT farm_namee FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
    )

    assert response == {
        "error": "ClickHouse error: Unknown identifier farm_namee",
    }


def test_execute_query_marks_result_as_truncated_at_limit():
    client = MagicMock()
    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [
        (1,),
        (2,),
        (3,),
    ]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
        limit=3,
    )

    assert response["row_count"] == 3
    assert response["limit"] == 3
    assert response["truncated"] is True


def test_execute_query_marks_result_as_not_truncated_below_limit():
    client = MagicMock()
    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [
        (1,),
        (2,),
    ]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
        limit=3,
    )

    assert response["row_count"] == 2
    assert response["truncated"] is False


def test_execute_query_rejects_invalid_caller_limit():
    client = MagicMock()

    response = execute_query(
        client,
        "SELECT farm_id FROM urbangreen_dw.dim_farm",
        default_limit=DEFAULT_LIMIT,
        max_limit=MAX_LIMIT,
        limit=0,
    )

    assert response == {
        "error": "Limit must be a positive integer.",
    }

    client.query.assert_not_called()
