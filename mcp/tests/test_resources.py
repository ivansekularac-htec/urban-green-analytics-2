"""
Tests for UrbanGreen MCP Markdown resources.

Covers live schema introspection and caching, static Markdown loading,
and the key metric and SQL convention rules exposed to the LLM.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from clickhouse_connect.driver.exceptions import OperationalError

import app.resources as resources
from app.resources import (
    get_conventions_resource,
    get_metrics_resource,
    get_schema_resource,
)


@pytest.fixture(autouse=True)
def reset_schema_cache():
    """Reset the schema cache around every test."""
    resources._schema_cache = None
    yield
    resources._schema_cache = None


@pytest.fixture(autouse=True)
def mock_settings(monkeypatch):
    """Use a stable ClickHouse database in resource tests."""
    settings = SimpleNamespace(clickhouse_db="urbangreen_dw")
    monkeypatch.setattr(resources, "get_settings", lambda: settings)


def _query_result(rows):
    """Build a minimal mocked ClickHouse query result."""
    result = MagicMock()
    result.result_rows = rows
    return result


# ---------------------------------------------------------------------------
# Schema resource
# ---------------------------------------------------------------------------


def test_schema_resource_builds_markdown_from_live_schema():
    client = MagicMock()

    client.query.return_value = _query_result(
        [
            (
                "dim_crop",
                (
                    "CREATE TABLE urbangreen_dw.dim_crop "
                    "(crop_id UInt64) "
                    "ENGINE = ReplacingMergeTree(_loaded_at) "
                    "ORDER BY crop_id"
                ),
            ),
            (
                "fact_harvests",
                (
                    "CREATE TABLE urbangreen_dw.fact_harvests "
                    "(harvest_id UInt64) "
                    "ENGINE = ReplacingMergeTree(_loaded_at) "
                    "ORDER BY harvest_id"
                ),
            ),
        ]
    )

    result = get_schema_resource(client)

    assert result.startswith("# UrbanGreen ClickHouse Schema")
    assert "`urbangreen_dw.dim_crop`" in result
    assert "`urbangreen_dw.fact_harvests`" in result
    assert "CREATE TABLE urbangreen_dw.dim_crop" in result
    assert "CREATE TABLE urbangreen_dw.fact_harvests" in result

    client.query.assert_called_once()


def test_schema_resource_reads_ddl_in_single_query():
    client = MagicMock()
    client.query.return_value = _query_result([])

    get_schema_resource(client)

    sql = client.query.call_args.args[0]

    assert "SELECT" in sql
    assert "name" in sql
    assert "create_table_query" in sql
    assert "FROM system.tables" in sql
    client.query.assert_called_once()


def test_schema_resource_uses_bound_parameters():
    client = MagicMock()
    client.query.return_value = _query_result([])

    get_schema_resource(client)

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in sql
    assert "{internal_prefix:String}" in sql
    assert parameters == {
        "database": "urbangreen_dw",
        "internal_prefix": ".inner",
    }


def test_schema_resource_uses_configured_database(monkeypatch):
    client = MagicMock()
    client.query.return_value = _query_result(
        [
            (
                "dim_crop",
                "CREATE TABLE test_warehouse.dim_crop (crop_id UInt64)",
            ),
        ]
    )

    settings = SimpleNamespace(clickhouse_db="test_warehouse")
    monkeypatch.setattr(resources, "get_settings", lambda: settings)

    result = get_schema_resource(client)

    parameters = client.query.call_args.kwargs["parameters"]

    assert parameters["database"] == "test_warehouse"
    assert "`test_warehouse.dim_crop`" in result
    assert "Live DDL for `test_warehouse`." in result


def test_schema_resource_filters_internal_tables():
    client = MagicMock()
    client.query.return_value = _query_result([])

    get_schema_resource(client)

    sql = client.query.call_args.args[0]

    assert "NOT startsWith(name, {internal_prefix:String})" in sql


def test_schema_resource_handles_empty_schema():
    client = MagicMock()
    client.query.return_value = _query_result([])

    result = get_schema_resource(client)

    assert result.startswith("# UrbanGreen ClickHouse Schema")
    assert "_No warehouse tables were found._" in result


def test_schema_resource_is_cached_after_successful_read():
    client = MagicMock()

    client.query.return_value = _query_result(
        [
            (
                "dim_crop",
                (
                    "CREATE TABLE urbangreen_dw.dim_crop "
                    "(crop_id UInt64) "
                    "ENGINE = ReplacingMergeTree(_loaded_at) "
                    "ORDER BY crop_id"
                ),
            ),
        ]
    )

    first = get_schema_resource(client)
    second = get_schema_resource(client)

    assert first == second
    client.query.assert_called_once()


def test_schema_resource_does_not_cache_failed_build():
    client = MagicMock()

    client.query.side_effect = [
        OperationalError("ClickHouse unavailable"),
        _query_result([]),
    ]

    first = get_schema_resource(client)

    assert "schema could not be read" in first
    assert "ClickHouse unavailable" in first
    assert resources._schema_cache is None

    second = get_schema_resource(client)

    assert second.startswith("# UrbanGreen ClickHouse Schema")
    assert "_No warehouse tables were found._" in second
    assert client.query.call_count == 2


# ---------------------------------------------------------------------------
# Static Markdown resources
# ---------------------------------------------------------------------------


def test_read_markdown_reads_and_strips_resource_file(tmp_path, monkeypatch):
    resource_dir = tmp_path / "resource_docs"
    resource_dir.mkdir()

    (resource_dir / "test.md").write_text(
        "\n# Test Resource\n\nSome content.\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(resources, "_RESOURCE_DIR", resource_dir)

    result = resources._read_markdown("test.md")

    assert result == "# Test Resource\n\nSome content."


def test_metrics_resource_reads_metrics_file(tmp_path, monkeypatch):
    resource_dir = tmp_path / "resource_docs"
    resource_dir.mkdir()

    (resource_dir / "metrics.md").write_text(
        "# UrbanGreen Metrics\n\nMetric content.",
        encoding="utf-8",
    )

    monkeypatch.setattr(resources, "_RESOURCE_DIR", resource_dir)

    result = get_metrics_resource()

    assert result == "# UrbanGreen Metrics\n\nMetric content."


def test_conventions_resource_reads_conventions_file(tmp_path, monkeypatch):
    resource_dir = tmp_path / "resource_docs"
    resource_dir.mkdir()

    (resource_dir / "conventions.md").write_text(
        "# UrbanGreen ClickHouse Conventions\n\nConvention content.",
        encoding="utf-8",
    )

    monkeypatch.setattr(resources, "_RESOURCE_DIR", resource_dir)

    result = get_conventions_resource()

    assert result == ("# UrbanGreen ClickHouse Conventions\n\nConvention content.")


# ---------------------------------------------------------------------------
# Metrics content
# ---------------------------------------------------------------------------


def test_metrics_document_sensor_average_reaggregation():
    result = get_metrics_resource()

    assert "fact_daily_sensor_metrics" in result
    assert "sum(sum_value)" in result
    assert "nullIf(sum(reading_count), 0)" in result
    assert "average of daily averages" in result


def test_metrics_document_leaderboard_is_precomputed():
    result = get_metrics_resource()

    assert "fact_farm_leaderboard" in result
    assert "Use the stored leaderboard values" in result
    assert "rather than recomputing ranks or scores" in result


def test_metrics_document_general_ratios_guard_zero_denominators():
    result = get_metrics_resource()

    assert "total_yield_kg / nullIf(size_m2, 0)" in result
    assert "energy_kwh / nullIf(total_yield_kg, 0)" in result


def test_metrics_document_leaderboard_zero_yield_behavior():
    result = get_metrics_resource()

    assert "energy_efficiency_kwh_per_kg = 0.0" in result
    assert "Zero-yield farms are explicitly ranked after farms with positive yield" in result


def test_metrics_document_identifies_canonical_sources():
    result = get_metrics_resource()

    assert "fact_daily_farm_metrics.total_yield_kg" in result
    assert "dim_farm.size_m2" in result
    assert "fact_farm_leaderboard" in result
    assert "fact_sensor_readings" in result


# ---------------------------------------------------------------------------
# Conventions content
# ---------------------------------------------------------------------------


def test_conventions_document_static_and_type1_dimension_rules():
    result = get_conventions_resource()

    assert "dim_date" in result
    assert "dim_time" in result
    assert "do not use `FINAL`" in result

    assert "dim_crop" in result
    assert "ReplacingMergeTree(_loaded_at)" in result
    assert "FINAL" in result
    assert "argMax" in result


def test_conventions_document_scd2_rules():
    result = get_conventions_resource()

    assert "ReplacingMergeTree(_version)" in result
    assert "valid_from" in result
    assert "valid_to" in result
    assert "is_current" in result

    assert "h.harvested_at >= f.valid_from" in result
    assert "h.harvested_at < f.valid_to" in result


def test_conventions_document_prefers_aggregate_facts():
    result = get_conventions_resource()

    assert "fact_daily_farm_metrics" in result
    assert "fact_daily_sensor_metrics" in result
    assert "fact_daily_farm_quality_metrics" in result
    assert "fact_farm_leaderboard" in result
    assert "instead of recomputing it from atomic facts" in result


def test_conventions_document_fact_deduplication_rule():
    result = get_conventions_resource()

    assert "ReplacingMergeTree(_loaded_at)" in result
    assert "Use `FINAL`" in result
