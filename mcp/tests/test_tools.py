"""
Unit tests for the core read-only ClickHouse tools.

Covers table discovery, schema inspection, safe query execution,
structured errors, parameter binding, and result limits.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.tools import describe_table, execute_query, list_tables


def _settings() -> SimpleNamespace:
    """Return test settings for query execution."""
    return SimpleNamespace(
        default_row_limit=100,
        max_row_limit=1000,
    )


def _query_result(
    *,
    rows=None,
    columns=None,
    row_count=None,
) -> MagicMock:
    """Build a mocked ClickHouse query result."""
    rows = [] if rows is None else rows
    columns = [] if columns is None else columns

    result = MagicMock()
    result.result_rows = rows
    result.column_names = columns
    result.row_count = len(rows) if row_count is None else row_count

    return result


def test_list_tables_returns_tables():
    """Return table names from an allowed database."""
    client = MagicMock()
    client.query.return_value = _query_result(
        rows=[
            ("dim_crop",),
            ("fact_harvests",),
        ]
    )

    result = list_tables(
        client,
        database="urbangreen_dw",
    )

    assert result == {
        "database": "urbangreen_dw",
        "tables": [
            "dim_crop",
            "fact_harvests",
        ],
    }


def test_list_tables_uses_bound_database_parameter():
    """Bind the database name instead of interpolating it into SQL."""
    client = MagicMock()
    client.query.return_value = _query_result()

    list_tables(
        client,
        database="urbangreen_dw",
    )

    client.query.assert_called_once()

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in sql
    assert parameters == {
        "database": "urbangreen_dw",
    }


@pytest.mark.parametrize(
    "database",
    ["urbangreen_dw", "etl"],
)
def test_list_tables_accepts_warehouse_databases(database):
    """Allow both configured warehouse databases."""
    client = MagicMock()
    client.query.return_value = _query_result()

    result = list_tables(
        client,
        database=database,
    )

    assert "error" not in result
    assert result["database"] == database


def test_list_tables_rejects_disallowed_database():
    """Reject databases outside the warehouse allow-list."""
    client = MagicMock()

    result = list_tables(
        client,
        database="system",
    )

    assert result["error"]["code"] == "DATABASE_NOT_ALLOWED"
    assert "system" in result["error"]["message"]

    client.query.assert_not_called()


def test_list_tables_returns_clickhouse_error():
    """Return a structured error when ClickHouse rejects the query."""
    client = MagicMock()
    client.query.side_effect = RuntimeError("ClickHouse unavailable")

    result = list_tables(client)

    assert result == {
        "error": {
            "code": "CLICKHOUSE_ERROR",
            "message": "ClickHouse unavailable",
        }
    }


def test_describe_table_returns_column_metadata():
    """Return column metadata for an existing table."""
    client = MagicMock()
    client.query.return_value = _query_result(
        rows=[
            (
                "farm_id",
                "UInt64",
                "",
                "",
                "Farm identifier",
            ),
            (
                "yield_kg",
                "Float64",
                "",
                "",
                "Harvest yield",
            ),
        ]
    )

    result = describe_table(
        client,
        table="fact_harvests",
        database="urbangreen_dw",
    )

    assert result == {
        "database": "urbangreen_dw",
        "table": "fact_harvests",
        "columns": [
            {
                "name": "farm_id",
                "type": "UInt64",
                "default_kind": "",
                "default_expression": "",
                "comment": "Farm identifier",
            },
            {
                "name": "yield_kg",
                "type": "Float64",
                "default_kind": "",
                "default_expression": "",
                "comment": "Harvest yield",
            },
        ],
    }


def test_describe_table_uses_bound_parameters():
    """Bind database and table names in the system-table query."""
    client = MagicMock()
    client.query.return_value = _query_result(
        rows=[
            (
                "farm_id",
                "UInt64",
                "",
                "",
                "",
            ),
        ]
    )

    describe_table(
        client,
        table="fact_harvests",
        database="urbangreen_dw",
    )

    client.query.assert_called_once()

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in sql
    assert "{table:String}" in sql

    assert parameters == {
        "database": "urbangreen_dw",
        "table": "fact_harvests",
    }


def test_describe_table_rejects_disallowed_database():
    """Reject schema inspection outside the warehouse databases."""
    client = MagicMock()

    result = describe_table(
        client,
        table="tables",
        database="system",
    )

    assert result["error"]["code"] == "DATABASE_NOT_ALLOWED"

    client.query.assert_not_called()


def test_describe_table_returns_error_for_unknown_table():
    """Return a structured error when the table does not exist."""
    client = MagicMock()
    client.query.return_value = _query_result()

    result = describe_table(
        client,
        table="missing_table",
        database="urbangreen_dw",
    )

    assert result["error"]["code"] == "TABLE_NOT_FOUND"
    assert "urbangreen_dw.missing_table" in result["error"]["message"]


def test_describe_table_returns_clickhouse_error():
    """Return a structured error when metadata lookup fails."""
    client = MagicMock()
    client.query.side_effect = RuntimeError("Metadata query failed")

    result = describe_table(
        client,
        table="fact_harvests",
    )

    assert result == {
        "error": {
            "code": "CLICKHOUSE_ERROR",
            "message": "Metadata query failed",
        }
    }


def test_execute_query_returns_structured_result():
    """Execute safe SQL and return rows with query metadata."""
    client = MagicMock()

    client.query.return_value = _query_result(
        rows=[
            (1, 10.5),
            (2, 20.5),
        ],
        columns=[
            "farm_id",
            "yield_kg",
        ],
    )

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT farm_id, yield_kg
            FROM urbangreen_dw.fact_harvests
            """,
        )

    assert result["limit"] == 100
    assert result["columns"] == [
        "farm_id",
        "yield_kg",
    ]
    assert result["rows"] == [
        (1, 10.5),
        (2, 20.5),
    ]
    assert result["row_count"] == 2
    assert result["truncated"] is False

    assert result["sql"].endswith("LIMIT 100")

    client.query.assert_called_once_with(result["sql"])


def test_execute_query_marks_result_as_truncated_at_limit():
    """Mark results as truncated when row count meets the applied limit."""
    client = MagicMock()

    client.query.return_value = _query_result(
        rows=[
            (1,),
            (2,),
        ],
        columns=["farm_id"],
        row_count=100,
    )

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT farm_id
            FROM urbangreen_dw.fact_harvests
            """,
        )

    assert result["limit"] == 100
    assert result["row_count"] == 100
    assert result["truncated"] is True


def test_execute_query_applies_caller_limit():
    """Apply a caller-supplied result limit."""
    client = MagicMock()

    client.query.return_value = _query_result(
        rows=[
            (1,),
            (2,),
        ],
        columns=["farm_id"],
    )

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT farm_id
            FROM urbangreen_dw.fact_harvests
            """,
            limit=50,
        )

    assert result["limit"] == 50
    assert result["sql"].endswith("LIMIT 50")


def test_execute_query_clamps_caller_limit_to_ceiling():
    """Clamp a caller limit to the configured maximum."""
    client = MagicMock()

    client.query.return_value = _query_result(
        rows=[],
        columns=["farm_id"],
    )

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT farm_id
            FROM urbangreen_dw.fact_harvests
            """,
            limit=5000,
        )

    assert result["limit"] == 1000
    assert result["sql"].endswith("LIMIT 1000")


def test_execute_query_clamps_sql_limit_to_caller_limit():
    """Do not allow SQL LIMIT to exceed the caller-supplied limit."""
    client = MagicMock()

    client.query.return_value = _query_result(
        rows=[],
        columns=["farm_id"],
    )

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT farm_id
            FROM urbangreen_dw.fact_harvests
            LIMIT 500
            """,
            limit=50,
        )

    assert result["limit"] == 50
    assert result["sql"].endswith("LIMIT 50")


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        True,
        "100",
    ],
)
def test_execute_query_rejects_invalid_caller_limit(limit):
    """Reject invalid caller-supplied limit values."""
    client = MagicMock()

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            "SELECT 1",
            limit=limit,
        )

    assert result["error"]["code"] == "INVALID_LIMIT"

    client.query.assert_not_called()


def test_execute_query_returns_sql_safety_error():
    """Return validation failures as structured error payloads."""
    client = MagicMock()

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            "DROP TABLE urbangreen_dw.fact_harvests",
        )

    assert result["error"]["code"] == "NOT_READ_ONLY"
    assert "read-only" in result["error"]["message"]

    client.query.assert_not_called()


def test_execute_query_rejects_multiple_statements():
    """Return a structured error for multiple SQL statements."""
    client = MagicMock()

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT 1;
            DROP TABLE urbangreen_dw.fact_harvests;
            """,
        )

    assert result["error"]["code"] == "MULTI_STATEMENT"

    client.query.assert_not_called()


def test_execute_query_rejects_query_settings():
    """Reject query-level SETTINGS through the SQL safety layer."""
    client = MagicMock()

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT *
            FROM urbangreen_dw.fact_harvests
            SETTINGS max_result_rows = 0
            """,
        )

    assert result["error"]["code"] == "SETTINGS_NOT_ALLOWED"

    client.query.assert_not_called()


def test_execute_query_returns_clickhouse_error():
    """Return ClickHouse execution failures as structured errors."""
    client = MagicMock()
    client.query.side_effect = RuntimeError("Query execution failed")

    with patch(
        "app.tools.get_settings",
        return_value=_settings(),
    ):
        result = execute_query(
            client,
            """
            SELECT *
            FROM urbangreen_dw.fact_harvests
            """,
        )

    assert result == {
        "error": {
            "code": "CLICKHOUSE_ERROR",
            "message": "Query execution failed",
        }
    }


def test_execute_query_returns_invalid_configuration_error():
    """Return invalid query-limit configuration as a structured error."""
    client = MagicMock()

    bad_settings = SimpleNamespace(
        default_row_limit=1000,
        max_row_limit=100,
    )

    with patch(
        "app.tools.get_settings",
        return_value=bad_settings,
    ):
        result = execute_query(
            client,
            "SELECT 1",
        )

    assert result["error"]["code"] == "INVALID_CONFIGURATION"
    assert "default_limit" in result["error"]["message"]

    client.query.assert_not_called()
