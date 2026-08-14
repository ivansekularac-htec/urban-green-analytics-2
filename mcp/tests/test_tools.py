"""Unit tests for the plain read-only ClickHouse tools."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from clickhouse_connect.driver.exceptions import DatabaseError

from app.tools import describe_table, execute_query, list_tables


def make_client(
    column_names: tuple[str, ...] = (),
    result_rows: list[tuple] | None = None,
) -> MagicMock:
    client = MagicMock()
    client.query.return_value = SimpleNamespace(
        column_names=column_names,
        result_rows=[] if result_rows is None else result_rows,
    )
    return client


def make_failing_client(message: str = "Code: 60. UNKNOWN_TABLE") -> MagicMock:
    client = MagicMock()
    client.query.side_effect = DatabaseError(message)
    return client


def test_list_tables_returns_tables():
    client = make_client(
        column_names=("name",),
        result_rows=[("dim_farm",), ("fact_sensor_reading",)],
    )

    result = list_tables(client)

    assert result == {
        "database": "urbangreen_dw",
        "tables": ["dim_farm", "fact_sensor_reading"],
        "table_count": 2,
    }


def test_list_tables_uses_a_bound_database_parameter():
    client = make_client()

    list_tables(client, database="etl")

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "etl" not in sql
    assert "{database:String}" in sql
    assert parameters == {"database": "etl"}


@pytest.mark.parametrize("database", ["system", "default", "information_schema", ""])
def test_list_tables_rejects_database_outside_allow_list(database):
    client = make_client()

    result = list_tables(client, database=database)

    assert result["error"]["code"] == "DATABASE_NOT_ALLOWED"
    client.query.assert_not_called()


def test_list_tables_returns_clickhouse_error():
    result = list_tables(make_failing_client("Connection unavailable"))

    assert result["error"] == {
        "code": "CLICKHOUSE_ERROR",
        "message": "Connection unavailable",
    }


def test_describe_table_returns_column_metadata():
    client = make_client(
        column_names=(
            "name",
            "type",
            "default_kind",
            "default_expression",
            "comment",
        ),
        result_rows=[
            ("farm_id", "UInt64", "", "", ""),
            ("name", "String", "DEFAULT", "''", "Farm name"),
        ],
    )

    result = describe_table(client, table="dim_farm")

    assert result == {
        "database": "urbangreen_dw",
        "table": "dim_farm",
        "columns": [
            {
                "name": "farm_id",
                "type": "UInt64",
                "default_kind": None,
                "default_expression": None,
                "comment": None,
            },
            {
                "name": "name",
                "type": "String",
                "default_kind": "DEFAULT",
                "default_expression": "''",
                "comment": "Farm name",
            },
        ],
    }


def test_describe_table_uses_bound_database_and_table_parameters():
    client = make_client(result_rows=[("run_id", "UUID", "", "", "")])

    describe_table(client, table="etl_runs", database="etl")

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "etl" not in sql
    assert "etl_runs" not in sql
    assert "{database:String}" in sql
    assert "{table:String}" in sql
    assert parameters == {"database": "etl", "table": "etl_runs"}


def test_describe_table_rejects_database_outside_allow_list():
    client = make_client()

    result = describe_table(client, table="tables", database="system")

    assert result["error"]["code"] == "DATABASE_NOT_ALLOWED"
    client.query.assert_not_called()


@pytest.mark.parametrize("table", ["", "   "])
def test_describe_table_rejects_missing_table_name(table):
    client = make_client()

    result = describe_table(client, table=table)

    assert result["error"]["code"] == "TABLE_NOT_FOUND"
    client.query.assert_not_called()


def test_describe_table_returns_error_for_unknown_table():
    client = make_client(result_rows=[])

    result = describe_table(client, table="unknown_table")

    assert result["error"]["code"] == "TABLE_NOT_FOUND"
    assert "urbangreen_dw.unknown_table" in result["error"]["message"]


def test_describe_table_returns_clickhouse_error():
    result = describe_table(make_failing_client("Query failed"), table="dim_farm")

    assert result["error"]["code"] == "CLICKHOUSE_ERROR"
    assert "Query failed" in result["error"]["message"]


def test_execute_query_returns_rewritten_sql_and_result_metadata():
    client = make_client(
        column_names=("farm_id", "name"),
        result_rows=[(1, "North Farm"), (2, "South Farm")],
    )

    result = execute_query(client, "SELECT farm_id, name FROM dim_farm")

    assert result == {
        "sql": "SELECT farm_id, name FROM dim_farm LIMIT 100",
        "limit": 100,
        "columns": ["farm_id", "name"],
        "rows": [[1, "North Farm"], [2, "South Farm"]],
        "row_count": 2,
        "truncated": False,
    }
    client.query.assert_called_once_with(result["sql"])


def test_execute_query_uses_configured_limits():
    client = make_client()
    settings = SimpleNamespace(default_row_limit=5, max_row_limit=20)

    with patch("app.tools.get_settings", return_value=settings):
        result = execute_query(client, "SELECT farm_id FROM dim_farm")

    assert result["sql"].endswith("LIMIT 5")
    assert result["limit"] == 5


def test_execute_query_clamps_caller_limit_to_configured_ceiling():
    client = make_client()
    settings = SimpleNamespace(default_row_limit=5, max_row_limit=20)

    with patch("app.tools.get_settings", return_value=settings):
        result = execute_query(
            client,
            "SELECT farm_id FROM dim_farm",
            limit=5000,
        )

    assert result["sql"].endswith("LIMIT 20")
    assert result["limit"] == 20


def test_execute_query_preserves_lower_limit_already_in_sql():
    client = make_client()

    result = execute_query(
        client,
        "SELECT farm_id FROM dim_farm LIMIT 5",
        limit=50,
    )

    assert result["sql"] == "SELECT farm_id FROM dim_farm LIMIT 5"
    assert result["limit"] == 5


@pytest.mark.parametrize("limit", [0, -1, True, "10"])
def test_execute_query_rejects_invalid_caller_limit(limit):
    client = make_client()

    result = execute_query(client, "SELECT 1", limit=limit)

    assert result["error"]["code"] == "INVALID_LIMIT"
    client.query.assert_not_called()


def test_execute_query_marks_result_truncated_when_limit_is_met():
    client = make_client(
        column_names=("value",),
        result_rows=[(1,), (2,)],
    )

    result = execute_query(client, "SELECT value FROM measurements", limit=2)

    assert result["row_count"] == 2
    assert result["limit"] == 2
    assert result["truncated"] is True


def test_execute_query_does_not_mark_metadata_result_truncated():
    client = make_client(
        column_names=("name",),
        result_rows=[("dim_farm",)],
    )

    result = execute_query(client, "SHOW TABLES")

    assert result["limit"] == 0
    assert result["truncated"] is False


@pytest.mark.parametrize(
    ("sql", "expected_code"),
    [
        ("", "EMPTY"),
        ("SELECT (", "UNPARSEABLE"),
        ("SELECT 1; SELECT 2", "MULTI_STATEMENT"),
        ("DROP TABLE events", "NOT_READ_ONLY"),
        ("SELECT * FROM events SETTINGS readonly = 0", "SETTINGS_NOT_ALLOWED"),
    ],
)
def test_execute_query_returns_safety_error_payload(sql, expected_code):
    client = make_client()

    result = execute_query(client, sql)

    assert result["error"]["code"] == expected_code
    client.query.assert_not_called()


def test_execute_query_returns_clickhouse_error():
    client = make_failing_client("Code: 164. READONLY")

    result = execute_query(client, "SELECT * FROM dim_farm")

    assert result["error"]["code"] == "CLICKHOUSE_ERROR"
    assert "READONLY" in result["error"]["message"]
