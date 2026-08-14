"""Tests for the read-only tools.

The ClickHouse client is a MagicMock throughout: these tests are about what the
tools hand back to the model, not about the driver.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from clickhouse_connect.driver.exceptions import DatabaseError

from app.tools import describe_table, execute_query, list_tables


def _client(column_names=(), result_rows=()) -> MagicMock:
    client = MagicMock()
    client.query.return_value = SimpleNamespace(
        column_names=column_names,
        result_rows=list(result_rows),
    )
    return client


def _failing_client(message: str = "Code: 60. Unknown table") -> MagicMock:
    client = MagicMock()
    client.query.side_effect = DatabaseError(message)
    return client


# --- list_tables ------------------------------------------------------------


def test_list_tables_returns_the_table_names():
    client = _client(column_names=("name",), result_rows=[("dim_farm",), ("fact_harvests",)])

    result = list_tables(client)

    assert result == {
        "database": "urbangreen_dw",
        "tables": ["dim_farm", "fact_harvests"],
        "table_count": 2,
    }


def test_list_tables_binds_the_database_as_a_parameter():
    """The database must travel as a bound parameter, not inside the SQL text."""

    client = _client(column_names=("name",), result_rows=[])

    list_tables(client, database="etl")

    _, kwargs = client.query.call_args
    assert kwargs["parameters"] == {"database": "etl"}
    assert "etl" not in client.query.call_args[0][0]


@pytest.mark.parametrize("database", ["system", "default", "information_schema", ""])
def test_list_tables_rejects_databases_outside_the_allow_list(database):
    client = _client()

    result = list_tables(client, database=database)

    assert result["error"]["code"] == "DATABASE_NOT_ALLOWED"
    client.query.assert_not_called()


def test_list_tables_returns_an_error_payload_when_clickhouse_fails():
    result = list_tables(_failing_client())

    assert result["error"]["code"] == "CLICKHOUSE_ERROR"
    assert "Unknown table" in result["error"]["message"]


# --- describe_table ---------------------------------------------------------


def test_describe_table_returns_the_columns():
    client = _client(
        column_names=("name", "type", "default_kind", "default_expression", "comment"),
        result_rows=[
            ("farm_id", "UInt64", "", "", ""),
            ("name", "String", "DEFAULT", "''", "farm name"),
        ],
    )

    result = describe_table(client, "dim_farm")

    assert result["database"] == "urbangreen_dw"
    assert result["table"] == "dim_farm"
    assert result["columns"] == [
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
            "comment": "farm name",
        },
    ]


def test_describe_table_binds_both_identifiers_as_parameters():
    client = _client(result_rows=[("a", "UInt8", "", "", "")])

    describe_table(client, "dim_farm", database="etl")

    _, kwargs = client.query.call_args
    assert kwargs["parameters"] == {"database": "etl", "table": "dim_farm"}
    assert "dim_farm" not in client.query.call_args[0][0]


def test_describe_table_rejects_a_database_outside_the_allow_list():
    client = _client()

    result = describe_table(client, "dim_farm", database="system")

    assert result["error"]["code"] == "DATABASE_NOT_ALLOWED"
    client.query.assert_not_called()


def test_describe_table_reports_an_unknown_table_instead_of_empty_columns():
    """No rows means the table does not exist, which the model must be told."""

    client = _client(result_rows=[])

    result = describe_table(client, "no_such_table")

    assert result["error"]["code"] == "TABLE_NOT_FOUND"
    assert "no_such_table" in result["error"]["message"]


@pytest.mark.parametrize("table", ["", "   "])
def test_describe_table_rejects_a_missing_table_name(table):
    client = _client()

    result = describe_table(client, table)

    assert result["error"]["code"] == "TABLE_NOT_FOUND"
    client.query.assert_not_called()


def test_describe_table_returns_an_error_payload_when_clickhouse_fails():
    result = describe_table(_failing_client(), "dim_farm")

    assert result["error"]["code"] == "CLICKHOUSE_ERROR"


# --- execute_query ----------------------------------------------------------


def test_execute_query_returns_the_rewritten_sql_and_rows():
    client = _client(column_names=("farm_id", "name"), result_rows=[(1, "UG Farm 001")])

    result = execute_query(client, "SELECT farm_id, name FROM dim_farm")

    assert result["sql"] == "SELECT farm_id, name FROM dim_farm LIMIT 100"
    assert result["limit"] == 100
    assert result["columns"] == ["farm_id", "name"]
    assert result["rows"] == [[1, "UG Farm 001"]]
    assert result["row_count"] == 1
    assert result["truncated"] is False
    client.query.assert_called_once_with(result["sql"])


def test_execute_query_flags_truncation_when_the_limit_is_reached():
    client = _client(column_names=("a",), result_rows=[(n,) for n in range(3)])

    result = execute_query(client, "SELECT a FROM t", limit=3)

    assert result["row_count"] == 3
    assert result["limit"] == 3
    assert result["truncated"] is True


def test_execute_query_clamps_a_caller_limit_to_the_ceiling():
    client = _client(column_names=("a",), result_rows=[])

    result = execute_query(client, "SELECT a FROM t", limit=999_999)

    assert result["sql"].endswith("LIMIT 1000")
    assert result["limit"] == 1000


def test_execute_query_leaves_an_explicit_limit_in_the_sql_alone():
    """The caller limit is a default, so a LIMIT the model wrote wins."""

    client = _client(column_names=("a",), result_rows=[])

    result = execute_query(client, "SELECT a FROM t LIMIT 5", limit=50)

    assert result["sql"] == "SELECT a FROM t LIMIT 5"
    assert result["limit"] == 5


@pytest.mark.parametrize("limit", [0, -1])
def test_execute_query_rejects_a_limit_below_one(limit):
    """The safety layer raises a plain ValueError for these, which is not an
    error the model could read, so they are caught before it is called."""

    client = _client()

    result = execute_query(client, "SELECT a FROM t", limit=limit)

    assert result["error"]["code"] == "INVALID_LIMIT"
    client.query.assert_not_called()


def test_execute_query_does_not_flag_truncation_for_metadata_statements():
    client = _client(column_names=("name",), result_rows=[("dim_farm",)])

    result = execute_query(client, "SHOW TABLES")

    assert result["limit"] == 0
    assert result["truncated"] is False


@pytest.mark.parametrize(
    ("sql", "code"),
    [
        ("", "EMPTY"),
        ("SELECT FROM", "UNPARSEABLE"),
        ("SELECT 1; SELECT 2", "MULTI_STATEMENT"),
        ("DROP TABLE t", "NOT_READ_ONLY"),
        ("OPTIMIZE TABLE t", "NOT_READ_ONLY"),
        ("SELECT a FROM t SETTINGS readonly = 0", "SETTINGS_NOT_ALLOWED"),
    ],
)
def test_execute_query_passes_safety_errors_through_as_payloads(sql, code):
    client = _client()

    result = execute_query(client, sql)

    assert result["error"]["code"] == code
    client.query.assert_not_called()


def test_execute_query_returns_an_error_payload_when_clickhouse_rejects_it():
    """A statement can pass the parser and still be refused by the server."""

    result = execute_query(_failing_client("Code: 164. READONLY"), "SELECT a FROM t")

    assert result["error"]["code"] == "CLICKHOUSE_ERROR"
    assert "READONLY" in result["error"]["message"]


def test_execute_query_reads_the_limits_from_settings():
    client = _client(column_names=("a",), result_rows=[])
    settings = SimpleNamespace(default_row_limit=5, max_row_limit=20)

    with patch("app.tools.get_settings", return_value=settings):
        injected = execute_query(client, "SELECT a FROM t")
        clamped = execute_query(client, "SELECT a FROM t", limit=999)

    assert injected["sql"].endswith("LIMIT 5")
    assert clamped["sql"].endswith("LIMIT 20")
