"""Tests for the model-facing warehouse Markdown resources."""

from unittest.mock import MagicMock, patch

import pytest

from app.resources import (
    get_conventions_markdown,
    get_metrics_markdown,
    get_schema_markdown,
)


def _query_result(*rows):
    result = MagicMock()
    result.result_rows = list(rows)
    return result


@pytest.fixture(autouse=True)
def clear_schema_cache():
    """Keep the process-lifetime schema cache isolated between unit tests."""
    get_schema_markdown.cache_clear()
    yield
    get_schema_markdown.cache_clear()


# ---------------------------------------------------------------------------
# Schema resource
# ---------------------------------------------------------------------------


def test_schema_is_loaded_lazily_and_cached_for_the_process():
    client = MagicMock()
    client.query.side_effect = [
        _query_result(("dim_farm",)),
        _query_result(("CREATE TABLE urbangreen_dw.dim_farm (farm_id UInt64)",)),
    ]

    with patch("app.resources.get_client", return_value=client) as get_client:
        get_client.assert_not_called()

        first = get_schema_markdown()
        second = get_schema_markdown()

    assert first == second
    get_client.assert_called_once_with()
    assert client.query.call_count == 2


def test_schema_introspects_tables_and_renders_show_create_output():
    client = MagicMock()
    client.query.side_effect = [
        _query_result(
            ("dim_farm",),
            ("fact_harvests",),
        ),
        _query_result(
            (
                "CREATE TABLE urbangreen_dw.dim_farm "
                "(farm_id UInt64) ENGINE = ReplacingMergeTree(_version) "
                "ORDER BY farm_id",
            )
        ),
        _query_result(
            (
                "CREATE TABLE urbangreen_dw.fact_harvests "
                "(harvest_id UInt64) ENGINE = ReplacingMergeTree(_loaded_at) "
                "ORDER BY harvest_id",
            )
        ),
    ]

    with patch("app.resources.get_client", return_value=client):
        markdown = get_schema_markdown()

    assert markdown.startswith("# UrbanGreen ClickHouse schema\n")
    assert "Database: `urbangreen_dw`" in markdown
    assert "## `dim_farm`" in markdown
    assert "## `fact_harvests`" in markdown
    assert "```sql\nCREATE TABLE urbangreen_dw.dim_farm" in markdown
    assert markdown.index("## `dim_farm`") < markdown.index("## `fact_harvests`")

    tables_call = client.query.call_args_list[0]
    assert "FROM system.tables" in tables_call.args[0]
    assert "NOT startsWith" in tables_call.args[0]
    assert "ORDER BY name" in tables_call.args[0]
    assert tables_call.kwargs["parameters"] == {
        "database": "urbangreen_dw",
        "internal_prefix": ".inner",
    }

    dim_ddl_call = client.query.call_args_list[1]
    assert dim_ddl_call.args[0] == ("SHOW CREATE TABLE {database:Identifier}.{table:Identifier}")
    assert dim_ddl_call.kwargs["parameters"] == {
        "database": "urbangreen_dw",
        "table": "dim_farm",
    }


def test_schema_defensively_filters_materialized_view_inner_tables():
    client = MagicMock()
    client.query.side_effect = [
        _query_result(
            (".inner.legacy_materialized_view",),
            (".inner_id.12345678-1234-1234-1234-123456789abc",),
            ("fact_daily_farm_metrics",),
        ),
        _query_result(("CREATE TABLE urbangreen_dw.fact_daily_farm_metrics (farm_id UInt64)",)),
    ]

    with patch("app.resources.get_client", return_value=client):
        markdown = get_schema_markdown()

    assert ".inner" not in markdown
    assert "## `fact_daily_farm_metrics`" in markdown
    assert client.query.call_count == 2
    assert client.query.call_args_list[1].kwargs["parameters"]["table"] == (
        "fact_daily_farm_metrics"
    )


def test_schema_does_not_cache_a_failed_build():
    client = MagicMock()
    client.query.side_effect = [
        _query_result(("dim_farm",)),
        _query_result(),
        _query_result(("dim_farm",)),
        _query_result(("CREATE TABLE urbangreen_dw.dim_farm (farm_id UInt64)",)),
    ]

    with patch("app.resources.get_client", return_value=client) as get_client:
        with pytest.raises(RuntimeError, match="returned no DDL"):
            get_schema_markdown()

        markdown = get_schema_markdown()

    assert "## `dim_farm`" in markdown
    assert get_client.call_count == 2
    assert client.query.call_count == 4


def test_schema_reports_when_no_visible_tables_exist():
    client = MagicMock()
    client.query.return_value = _query_result()

    with patch("app.resources.get_client", return_value=client):
        markdown = get_schema_markdown()

    assert "No user-visible tables were found." in markdown
    client.query.assert_called_once()


# ---------------------------------------------------------------------------
# Metrics resource
# ---------------------------------------------------------------------------


def test_metrics_document_current_dashboard_definitions():
    markdown = get_metrics_markdown()

    assert markdown.startswith("# UrbanGreen canonical metrics\n")
    assert "## Executive Overview" in markdown
    assert "## Operations Overview" in markdown
    assert "## Farm Overview" in markdown
    assert "## Auditor Overview" in markdown
    assert "### Profitability Index" in markdown
    assert "sumIf(weight_kg, is_high_value = 1)" in markdown
    assert "### Farm Performance Leaderboard" in markdown
    assert "farm_count - axis_rank + 1" in markdown
    assert "24 * SUM(in_range_count)" in markdown
    assert "SUM(non_premium_yield_kg)" in markdown


def test_metrics_distinguish_high_value_crops_from_premium_quality():
    markdown = get_metrics_markdown()

    assert "Do not substitute premium quality grades" in markdown
    assert "premium share is" in markdown
    assert "premium_yield_kg / total_yield_kg" in markdown


# ---------------------------------------------------------------------------
# Conventions resource
# ---------------------------------------------------------------------------


def test_conventions_match_the_current_replacing_merge_tree_design():
    markdown = get_conventions_markdown()

    assert markdown.startswith("# UrbanGreen ClickHouse query conventions\n")
    assert "ReplacingMergeTree(_loaded_at)" in markdown
    assert "fact_daily_farm_metrics FINAL" in markdown
    assert "Type-1 reference dimensions use `_loaded_at`" in markdown
    assert "SCD2 dimensions preserve history" in markdown
    assert "WHERE is_current = 1" in markdown
    assert "h.harvested_at >= f.valid_from" in markdown
    assert "h.harvested_at < f.valid_to" in markdown


def test_conventions_exempt_static_dimensions_and_define_safe_reaggregation():
    markdown = get_conventions_markdown()

    assert "Static calendar dimensions do not need `FINAL`" in markdown
    assert "urbangreen_dw.dim_date AS d" in markdown
    assert "sum(sum_value) / nullIf(sum(reading_count), 0)" in markdown
    assert "Do not average daily averages" in markdown
    assert "Use `nullIf(denominator, 0)`" in markdown
