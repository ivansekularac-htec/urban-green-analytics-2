"""
Tests for UrbanGreen MCP Markdown resources.

Covers live schema introspection and caching, static Markdown loading,
and the key metric and SQL convention rules exposed to the LLM.
"""

from unittest.mock import MagicMock

import pytest

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
            ("dim_crop",),
            ("fact_harvests",),
        ]
    )

    client.command.side_effect = [
        (
            "CREATE TABLE urbangreen_dw.dim_crop "
            "(crop_id UInt64) "
            "ENGINE = ReplacingMergeTree(_loaded_at) "
            "ORDER BY crop_id"
        ),
        (
            "CREATE TABLE urbangreen_dw.fact_harvests "
            "(harvest_id UInt64) "
            "ENGINE = ReplacingMergeTree(_loaded_at) "
            "ORDER BY harvest_id"
        ),
    ]

    result = get_schema_resource(client)

    assert result.startswith("# UrbanGreen ClickHouse Schema")
    assert "`urbangreen_dw.dim_crop`" in result
    assert "`urbangreen_dw.fact_harvests`" in result
    assert "CREATE TABLE urbangreen_dw.dim_crop" in result
    assert "CREATE TABLE urbangreen_dw.fact_harvests" in result

    client.query.assert_called_once()
    assert client.command.call_count == 2


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


def test_schema_resource_filters_internal_tables():
    client = MagicMock()
    client.query.return_value = _query_result([])

    get_schema_resource(client)

    sql = client.query.call_args.args[0]

    assert "FROM system.tables" in sql
    assert "NOT startsWith(name, {internal_prefix:String})" in sql


def test_schema_resource_handles_empty_schema():
    client = MagicMock()
    client.query.return_value = _query_result([])

    result = get_schema_resource(client)

    assert result.startswith("# UrbanGreen ClickHouse Schema")
    assert "_No warehouse tables were found._" in result
    client.command.assert_not_called()


def test_schema_resource_is_cached_after_successful_read():
    client = MagicMock()

    client.query.return_value = _query_result(
        [
            ("dim_crop",),
        ]
    )

    client.command.return_value = (
        "CREATE TABLE urbangreen_dw.dim_crop "
        "(crop_id UInt64) "
        "ENGINE = ReplacingMergeTree(_loaded_at) "
        "ORDER BY crop_id"
    )

    first = get_schema_resource(client)
    second = get_schema_resource(client)

    assert first == second
    client.query.assert_called_once()
    client.command.assert_called_once()


def test_schema_resource_does_not_cache_failed_build():
    client = MagicMock()

    client.query.side_effect = [
        RuntimeError("ClickHouse unavailable"),
        _query_result([]),
    ]

    with pytest.raises(RuntimeError, match="ClickHouse unavailable"):
        get_schema_resource(client)

    assert resources._schema_cache is None

    result = get_schema_resource(client)

    assert result.startswith("# UrbanGreen ClickHouse Schema")
    assert client.query.call_count == 2


def test_schema_resource_does_not_cache_partial_build():
    client = MagicMock()

    client.query.return_value = _query_result(
        [
            ("dim_crop",),
            ("fact_harvests",),
        ]
    )

    client.command.side_effect = [
        "CREATE TABLE urbangreen_dw.dim_crop (crop_id UInt64)",
        RuntimeError("SHOW CREATE failed"),
    ]

    with pytest.raises(RuntimeError, match="SHOW CREATE failed"):
        get_schema_resource(client)

    assert resources._schema_cache is None


def test_schema_resource_quotes_database_and_table_names():
    client = MagicMock()

    client.query.return_value = _query_result(
        [
            ("dim_crop",),
        ]
    )
    client.command.return_value = "CREATE TABLE dim_crop"

    get_schema_resource(client)

    client.command.assert_called_once_with("SHOW CREATE TABLE `urbangreen_dw`.`dim_crop`")


def test_quote_identifier_escapes_backticks():
    assert resources._quote_identifier("some`table") == "`some``table`"


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


def test_metrics_document_premium_yield_share():
    result = get_metrics_resource()

    assert "premium_yield_share" in result
    assert "premium_yield_kg / total_yield_kg" in result
    assert "dim_quality_grade.is_premium = 1" in result


def test_metrics_document_energy_efficiency():
    result = get_metrics_resource()

    assert "energy_efficiency_kwh_per_kg" in result
    assert "energy_kwh / total_yield_kg" in result
    assert "zero yield" in result.lower()


def test_metrics_document_sensor_average_reaggregation():
    result = get_metrics_resource()

    assert "fact_daily_sensor_metrics" in result
    assert "sum(sum_value)" in result
    assert "sum(reading_count)" in result
    assert "nullIf" in result
    assert "average of daily averages" in result


def test_metrics_document_precomputed_leaderboard_rules():
    result = get_metrics_resource()

    assert "fact_farm_leaderboard" in result
    assert "yield_rank" in result
    assert "quality_rank" in result
    assert "energy_rank" in result
    assert "composite_rank" in result
    assert "Spark `rank()`" in result


def test_metrics_document_leaderboard_should_not_be_recomputed():
    result = get_metrics_resource()

    assert "Use the stored leaderboard values" in result
    assert "rather than recomputing ranks or scores" in result
    assert "composite_score" in result
    assert "equal-weight score" in result


# ---------------------------------------------------------------------------
# Conventions content
# ---------------------------------------------------------------------------


def test_conventions_document_static_dimensions():
    result = get_conventions_resource()

    assert "dim_date" in result
    assert "dim_time" in result
    assert "plain `MergeTree`" in result
    assert "do not use `FINAL`" in result


def test_conventions_document_type1_dimensions():
    result = get_conventions_resource()

    assert "dim_role" in result
    assert "dim_quality_grade" in result
    assert "dim_crop" in result
    assert "dim_user" in result
    assert "ReplacingMergeTree(_loaded_at)" in result
    assert "FINAL" in result
    assert "argMax" in result


def test_conventions_document_scd2_dimensions():
    result = get_conventions_resource()

    assert "dim_farm" in result
    assert "dim_user_farm_role" in result
    assert "dim_sensor" in result
    assert "dim_sensor_type" in result
    assert "ReplacingMergeTree(_version)" in result
    assert "valid_from" in result
    assert "valid_to" in result
    assert "is_current" in result


def test_conventions_document_historical_scd2_join():
    result = get_conventions_resource()

    assert "h.harvested_at >= f.valid_from" in result
    assert "h.harvested_at < f.valid_to" in result
    assert "fact_harvests AS h FINAL" in result
    assert "dim_farm AS f FINAL" in result


def test_conventions_document_atomic_facts():
    result = get_conventions_resource()

    assert "Atomic facts" in result
    assert "fact_harvests" in result
    assert "fact_sensor_readings" in result
    assert "event-level detail" in result


def test_conventions_document_aggregate_facts():
    result = get_conventions_resource()

    assert "Aggregate facts" in result
    assert "fact_daily_farm_metrics" in result
    assert "fact_daily_sensor_metrics" in result
    assert "fact_daily_farm_quality_metrics" in result
    assert "fact_farm_leaderboard" in result
    assert "instead of recomputing it from atomic facts" in result


def test_conventions_document_fact_table_behavior():
    result = get_conventions_resource()

    assert "Fact table behavior" in result
    assert "ReplacingMergeTree(_loaded_at)" in result
    assert "idempotent Spark reloads" in result
    assert "background merge" in result
    assert "Use `FINAL`" in result
