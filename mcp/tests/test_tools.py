"""Tests for the read-only ClickHouse core tools."""

from unittest.mock import MagicMock, patch

import pytest
from clickhouse_connect.driver.client import Client
from clickhouse_connect.driver.exceptions import ClickHouseError

from app.tools import describe_table, execute_query, list_tables


def test_list_tables_returns_tables():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.result_rows = [
        ("dim_farm",),
        ("fact_harvests",),
    ]
    client.query.return_value = result

    response = list_tables(client, "urbangreen_dw")

    assert response == {
        "database": "urbangreen_dw",
        "tables": ["dim_farm", "fact_harvests"],
    }

    client.query.assert_called_once()


def test_list_tables_uses_bound_parameters():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.result_rows = [("dim_farm",)]
    client.query.return_value = result

    list_tables(client, "urbangreen_dw")

    query = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in query
    assert parameters == {
        "database": "urbangreen_dw",
    }


def test_list_tables_rejects_unknown_database():
    client = MagicMock(spec=Client)

    response = list_tables(client, "default")

    assert response["error"]["code"] == "INVALID_DATABASE"
    client.query.assert_not_called()


def test_list_tables_returns_error_when_query_fails():
    client = MagicMock(spec=Client)
    client.query.side_effect = RuntimeError("connection failed")

    response = list_tables(client, "urbangreen_dw")

    assert response == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected error while listing tables.",
        }
    }


def test_list_tables_returns_clickhouse_error():
    client = MagicMock(spec=Client)
    client.query.side_effect = ClickHouseError("query failed")

    response = list_tables(client, "urbangreen_dw")

    assert response == {
        "error": {
            "code": "CLICKHOUSE_ERROR",
            "message": "query failed",
        }
    }


def test_describe_table_returns_column_metadata():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.result_rows = [
        ("farm_id", "UInt64", "", "", "Source identifier of the farm.", 1, 1, 0),
        ("name", "String", "", "", "Farm name.", 0, 0, 0),
        ("city", "String", "DEFAULT", "'Unknown'", "City where the farm is located.", 0, 0, 1),
    ]
    client.query.return_value = result

    response = describe_table(client, "dim_farm", "urbangreen_dw")

    assert response == {
        "database": "urbangreen_dw",
        "table": "dim_farm",
        "columns": [
            {
                "name": "farm_id",
                "type": "UInt64",
                "default_kind": "",
                "default_expression": "",
                "comment": "Source identifier of the farm.",
                "is_primary_key": True,
                "is_sorting_key": True,
                "is_partition_key": False,
            },
            {
                "name": "name",
                "type": "String",
                "default_kind": "",
                "default_expression": "",
                "comment": "Farm name.",
                "is_primary_key": False,
                "is_sorting_key": False,
                "is_partition_key": False,
            },
            {
                "name": "city",
                "type": "String",
                "default_kind": "DEFAULT",
                "default_expression": "'Unknown'",
                "comment": "City where the farm is located.",
                "is_primary_key": False,
                "is_sorting_key": False,
                "is_partition_key": True,
            },
        ],
    }


def test_describe_table_uses_bound_parameters():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.result_rows = [
        ("farm_id", "UInt64", "", "", "Source identifier of the farm.", 1, 1, 0),
    ]
    client.query.return_value = result

    describe_table(client, "dim_farm", "urbangreen_dw")

    query = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in query
    assert "{table:String}" in query
    assert parameters == {
        "database": "urbangreen_dw",
        "table": "dim_farm",
    }


def test_describe_table_rejects_unknown_database():
    client = MagicMock(spec=Client)

    response = describe_table(client, "dim_farm", "default")

    assert response["error"]["code"] == "INVALID_DATABASE"
    assert "default" in response["error"]["message"]

    client.query.assert_not_called()


def test_describe_table_returns_error_for_unknown_table():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.result_rows = []
    client.query.return_value = result

    response = describe_table(client, "missing_table", "urbangreen_dw")

    assert response == {
        "error": {
            "code": "TABLE_NOT_FOUND",
            "message": ("Table 'missing_table' was not found in database 'urbangreen_dw'."),
        }
    }


def test_describe_table_returns_clickhouse_error():
    client = MagicMock(spec=Client)
    client.query.side_effect = ClickHouseError("query failed")

    response = describe_table(client, "dim_farm", "urbangreen_dw")

    assert response == {
        "error": {
            "code": "CLICKHOUSE_ERROR",
            "message": "query failed",
        }
    }


def test_describe_table_returns_internal_error():
    client = MagicMock(spec=Client)
    client.query.side_effect = RuntimeError("unexpected failure")

    response = describe_table(client, "dim_farm", "urbangreen_dw")

    assert response == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected error while describing table.",
        }
    }


def test_execute_query_returns_result_with_default_limit():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.column_names = ("farm_id", "name")
    result.result_rows = [
        (1, "Farm A"),
        (2, "Farm B"),
    ]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id, name FROM dim_farm",
    )

    assert response == {
        "sql": "SELECT farm_id, name FROM dim_farm LIMIT 100",
        "limit": 100,
        "columns": ["farm_id", "name"],
        "rows": [
            (1, "Farm A"),
            (2, "Farm B"),
        ],
        "row_count": 2,
        "truncated": False,
    }

    client.query.assert_called_once_with("SELECT farm_id, name FROM dim_farm LIMIT 100")


def test_execute_query_marks_result_as_truncated_when_limit_is_reached():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [
        (1,),
        (2,),
    ]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM dim_farm",
        limit=2,
    )

    assert response["limit"] == 2
    assert response["row_count"] == 2
    assert response["truncated"] is True


def test_execute_query_applies_caller_limit():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [(1,)]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM dim_farm",
        limit=25,
    )

    assert response["sql"] == "SELECT farm_id FROM dim_farm LIMIT 25"
    assert response["limit"] == 25

    client.query.assert_called_once_with("SELECT farm_id FROM dim_farm LIMIT 25")


def test_execute_query_clamps_caller_limit_to_configured_maximum():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [(1,)]
    client.query.return_value = result

    settings = MagicMock()
    settings.default_row_limit = 25
    settings.max_row_limit = 200

    with patch("app.tools.get_settings", return_value=settings):
        response = execute_query(
            client,
            "SELECT farm_id FROM dim_farm",
            limit=5000,
        )

    assert response["sql"] == "SELECT farm_id FROM dim_farm LIMIT 200"
    assert response["limit"] == 200


def test_execute_query_preserves_smaller_sql_limit():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [(1,)]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM dim_farm LIMIT 10",
        limit=50,
    )

    assert response["sql"] == "SELECT farm_id FROM dim_farm LIMIT 10"
    assert response["limit"] == 10


def test_execute_query_clamps_sql_limit_to_caller_limit():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.column_names = ("farm_id",)
    result.result_rows = [(1,)]
    client.query.return_value = result

    response = execute_query(
        client,
        "SELECT farm_id FROM dim_farm LIMIT 100",
        limit=25,
    )

    assert response["sql"] == "SELECT farm_id FROM dim_farm LIMIT 25"
    assert response["limit"] == 25


def test_execute_query_returns_sql_safety_error():
    client = MagicMock(spec=Client)

    response = execute_query(
        client,
        "DROP TABLE dim_farm",
    )

    assert "error" in response
    assert response["error"]["code"] == "NOT_READ_ONLY"

    client.query.assert_not_called()


def test_execute_query_returns_clickhouse_error():
    client = MagicMock(spec=Client)
    client.query.side_effect = ClickHouseError("Unknown identifier")

    response = execute_query(
        client,
        "SELECT missing_column FROM dim_farm",
    )

    assert response == {
        "error": {
            "code": "CLICKHOUSE_ERROR",
            "message": "Unknown identifier",
        }
    }


def test_execute_query_returns_internal_error_when_execution_fails():
    client = MagicMock(spec=Client)
    client.query.side_effect = RuntimeError("unexpected failure")

    response = execute_query(
        client,
        "SELECT * FROM dim_farm",
    )

    assert response == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected error while executing query.",
        }
    }


def test_execute_query_returns_internal_error_when_validation_fails():
    client = MagicMock(spec=Client)

    with patch(
        "app.tools.validate_and_rewrite_sql",
        side_effect=RuntimeError("unexpected validation failure"),
    ):
        response = execute_query(
            client,
            "SELECT * FROM dim_farm",
        )

    assert response == {
        "error": {
            "code": "INTERNAL_ERROR",
            "message": "Unexpected error while validating query.",
        }
    }

    client.query.assert_not_called()


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        1.5,
        "10",
        True,
    ],
)
def test_execute_query_rejects_invalid_caller_limit(limit):
    client = MagicMock(spec=Client)

    response = execute_query(
        client,
        "SELECT * FROM dim_farm",
        limit=limit,
    )

    assert response == {
        "error": {
            "code": "INVALID_LIMIT",
            "message": "Limit must be a positive integer.",
        }
    }

    client.query.assert_not_called()


def test_execute_query_does_not_mark_metadata_result_as_truncated():
    client = MagicMock(spec=Client)

    result = MagicMock()
    result.column_names = ("name",)
    result.result_rows = [
        ("dim_farm",),
        ("fact_harvests",),
    ]
    client.query.return_value = result

    response = execute_query(
        client,
        "SHOW TABLES FROM urbangreen_dw",
    )

    assert response["limit"] == 0
    assert response["row_count"] == 2
    assert response["truncated"] is False
