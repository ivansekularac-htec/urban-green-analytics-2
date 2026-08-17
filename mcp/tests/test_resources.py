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


def test_metrics_document_shared_rules():
    result = get_metrics_resource()

    assert "dim_quality_grade.is_premium = 1" in result
    assert "Energy Usage" in result
    assert "fact_daily_sensor_metrics" in result
    assert "sum(sum_value)" in result
    assert "sum(reading_count)" in result
    assert "nullIf" in result
    assert "average of daily averages" in result


def test_metrics_document_executive_metrics():
    result = get_metrics_resource()

    assert "## Executive Overview" in result
    assert "### Total Harvest Yield" in result
    assert "### Yield Efficiency" in result
    assert "### Weekly Yield Trend" in result
    assert "### Harvest Quality Mix" in result
    assert "### Profitability Index" in result
    assert "### Farm Expansion Progress" in result
    assert "### Energy Efficiency" in result
    assert "### City/Region Performance" in result
    assert "### Top Crop per City" in result


def test_metrics_document_yield_efficiency():
    result = get_metrics_resource()

    assert "yield_efficiency" in result
    assert "total_yield_kg / nullIf(size_m2, 0)" in result
    assert "kg/m²" in result


def test_metrics_document_energy_efficiency():
    result = get_metrics_resource()

    assert "energy_efficiency_kwh_per_kg" in result
    assert "energy_kwh / nullIf(total_yield_kg, 0)" in result
    assert "kWh/kg" in result


def test_metrics_document_farm_expansion_target():
    result = get_metrics_resource()

    assert "Farm Expansion Progress" in result
    assert "target of `100`" in result


def test_metrics_document_operations_metrics():
    result = get_metrics_resource()

    assert "## Operations Overview" in result
    assert "### Farm Performance Leaderboard" in result
    assert "### Live Sensor Anomaly Alerts" in result
    assert "### Sensor Anomaly Rate Trend" in result
    assert "### Sensor Coverage Health Index" in result
    assert "### Data Freshness Heatmap" in result
    assert "### Environmental Compliance Rate" in result
    assert "### Crop Yield by Farm" in result
    assert "### Harvest Quality Breakdown" in result
    assert "### Inactive/Faulty Sensors" in result


def test_metrics_document_precomputed_leaderboard_rules():
    result = get_metrics_resource()

    assert "fact_farm_leaderboard" in result
    assert "Use the stored leaderboard values" in result
    assert "rather than recomputing ranks or scores" in result
    assert "yield_rank" in result
    assert "quality_rank" in result
    assert "energy_rank" in result
    assert "composite_score" in result
    assert "composite_rank" in result
    assert "premium_yield_share" in result
    assert "Spark `rank()`" in result


def test_metrics_document_leaderboard_zero_yield_behavior():
    result = get_metrics_resource()

    assert "premium_yield_share = 0.0" in result
    assert "energy_efficiency_kwh_per_kg = 0.0" in result
    assert "Zero-yield farms are explicitly ranked after farms with positive yield" in result
    assert "Do not interpret the stored energy value as perfect" in result


def test_metrics_document_anomaly_rate():
    result = get_metrics_resource()

    assert "anomaly_rate" in result
    assert "anomaly_count / nullIf(reading_count, 0)" in result


def test_metrics_document_sensor_coverage():
    result = get_metrics_resource()

    assert "sensor_coverage" in result
    assert "active_sensor_count / nullIf(total_sensor_count, 0)" in result


def test_metrics_document_environmental_compliance():
    result = get_metrics_resource()

    assert "compliance_rate" in result
    assert "in_range_count / nullIf(reading_count, 0)" in result


def test_metrics_document_data_freshness():
    result = get_metrics_resource()

    assert "Data Freshness Heatmap" in result
    assert "latest sensor reading" in result
    assert "Smaller time gaps indicate fresher data" in result


def test_metrics_document_farm_overview_metrics():
    result = get_metrics_resource()

    assert "## Farm Overview" in result
    assert "### Live Environmental Gauges" in result
    assert "### Today's / This Week's Harvest" in result
    assert "### Crop-Level Yield" in result
    assert "### Best Performing Crop" in result
    assert "### Yield-per-Bed" in result
    assert "### Harvest Quality Report" in result
    assert "### Resource Consumption Trend" in result
    assert "### Light Hour Compliance" in result
    assert "### Sensor Data History" in result


def test_metrics_document_yield_per_bed():
    result = get_metrics_resource()

    assert "yield_per_bed" in result
    assert "total_yield_kg / nullIf(growing_beds_count, 0)" in result


def test_metrics_document_auditor_metrics():
    result = get_metrics_resource()

    assert "## Auditor Overview" in result
    assert "### Total Energy Consumption" in result
    assert "### Energy Efficiency" in result
    assert "### Waste Reduction Progress" in result
    assert "### CO2 Concentration Levels" in result
    assert "### CO2 Compliance Rate" in result


def test_metrics_document_waste_reduction():
    result = get_metrics_resource()

    assert "waste_reduction_progress" in result
    assert "non_premium_yield_kg / nullIf(total_yield_kg, 0)" in result


def test_metrics_document_co2_compliance():
    result = get_metrics_resource()

    assert "CO2 Compliance Rate" in result
    assert "400–1200 ppm" in result
    assert "compliant_co2_readings / nullIf(total_co2_readings, 0)" in result


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
