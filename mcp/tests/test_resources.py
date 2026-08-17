"""Tests for the model-facing warehouse Markdown resources."""

from unittest.mock import MagicMock

import pytest

from app.resources import (
    build_schema_markdown,
    get_conventions_markdown,
    get_metrics_markdown,
)


def _query_result(*rows):
    result = MagicMock()
    result.result_rows = list(rows)
    return result


# ---------------------------------------------------------------------------
# Schema resource
# ---------------------------------------------------------------------------


def test_schema_introspects_tables_and_renders_catalog_ddl():
    client = MagicMock()
    client.query.return_value = _query_result(
        (
            "dim_farm",
            "CREATE TABLE urbangreen_dw.dim_farm "
            "(farm_id UInt64) ENGINE = ReplacingMergeTree(_version) "
            "ORDER BY farm_id",
        ),
        (
            "fact_harvests",
            "CREATE TABLE urbangreen_dw.fact_harvests "
            "(harvest_id UInt64) ENGINE = ReplacingMergeTree(_loaded_at) "
            "ORDER BY harvest_id",
        ),
    )

    markdown = build_schema_markdown(client)

    assert markdown.startswith("# UrbanGreen ClickHouse schema\n")
    assert "Database: `urbangreen_dw`" in markdown
    assert "## `dim_farm`" in markdown
    assert "## `fact_harvests`" in markdown
    assert "```sql\nCREATE TABLE urbangreen_dw.dim_farm" in markdown
    assert markdown.index("## `dim_farm`") < markdown.index("## `fact_harvests`")

    client.query.assert_called_once()

    catalog_call = client.query.call_args
    sql = catalog_call.args[0]

    assert "create_table_query" in sql
    assert "FROM system.tables" in sql
    assert "SHOW CREATE TABLE" not in sql
    assert catalog_call.kwargs["parameters"] == {"database": "urbangreen_dw"}


def test_schema_catalog_query_filters_internal_materialized_view_tables():
    client = MagicMock()
    client.query.return_value = _query_result(
        (
            "fact_daily_farm_metrics",
            "CREATE TABLE urbangreen_dw.fact_daily_farm_metrics (farm_id UInt64)",
        )
    )

    markdown = build_schema_markdown(client)

    assert "## `fact_daily_farm_metrics`" in markdown
    client.query.assert_called_once()

    sql = " ".join(client.query.call_args.args[0].split())

    assert sql == (
        "SELECT name, create_table_query "
        "FROM system.tables "
        "WHERE database = {database:String} "
        "AND name NOT LIKE '.inner%' "
        "ORDER BY name"
    )

    assert client.query.call_args.kwargs["parameters"] == {"database": "urbangreen_dw"}


def test_schema_builder_propagates_catalog_errors():
    client = MagicMock()
    client.query.side_effect = RuntimeError("Catalog query failed")

    with pytest.raises(RuntimeError, match="Catalog query failed"):
        build_schema_markdown(client)

    client.query.assert_called_once()


def test_schema_reports_when_no_visible_tables_exist():
    client = MagicMock()
    client.query.return_value = _query_result()

    markdown = build_schema_markdown(client)

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
    assert "read the stored rank and score columns" in markdown
    assert "Do not recompute or rerank" in markdown
    assert "farm_count - axis_rank + 1" not in markdown
    assert "24 * SUM(in_range_count)" in markdown
    assert "SUM(non_premium_yield_kg)" in markdown
    assert "grade code `A` as premium" in markdown
    assert "every other grade code counts as non-premium" in markdown


def test_metrics_distinguish_high_value_crops_from_premium_quality():
    markdown = get_metrics_markdown()
    normalized = " ".join(markdown.split())

    assert "Do not substitute premium quality grades" in markdown
    assert "`premium_yield_share` is the farm's premium-quality yield share" in normalized
    assert "grade code `A` as premium" in normalized
    assert "every other grade code counts as non-premium" in normalized


# ---------------------------------------------------------------------------
# Conventions resource
# ---------------------------------------------------------------------------


def test_conventions_match_the_current_replacing_merge_tree_design():
    markdown = get_conventions_markdown()
    normalized = " ".join(markdown.split())

    assert markdown.startswith("# UrbanGreen ClickHouse query conventions\n")
    assert "ReplacingMergeTree(_loaded_at)" in markdown
    assert "fact_daily_farm_metrics FINAL" in markdown
    assert "Type-1 reference dimensions use `_loaded_at`" in markdown
    assert "SCD2 dimensions preserve history" in markdown
    assert "WHERE is_current = 1" in markdown
    assert "h.harvested_at >= f.valid_from" in markdown
    assert "h.harvested_at < f.valid_to" in markdown
    assert "For historical attributes or relationships" in normalized
    assert "use atomic fact timestamps for accurate attribution" in normalized
    assert "cannot be divided reliably between multiple dimension versions" in normalized


def test_conventions_exempt_static_dimensions_and_define_safe_reaggregation():
    markdown = get_conventions_markdown()

    assert "Static calendar dimensions do not need `FINAL`" in markdown
    assert "urbangreen_dw.dim_date AS d" in markdown
    assert "sum(sum_value) / nullIf(sum(reading_count), 0)" in markdown
    assert "Do not average daily averages" in markdown
    assert "Use `nullIf(denominator, 0)`" in markdown
