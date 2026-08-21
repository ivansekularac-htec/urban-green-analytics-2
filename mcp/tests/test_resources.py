"""Tests for the Markdown knowledge resources."""

import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.resources import (
    conventions_resource,
    load_schema_markdown,
    metrics_resource,
    render_schema_markdown,
)

RESOURCE_DOCS_DIR = Path(__file__).parents[1] / "app" / "resource_docs"


def make_client(
    table_ddls: dict[str, str],
) -> MagicMock:
    client = MagicMock()

    client.query.return_value = SimpleNamespace(result_rows=list(table_ddls.items()))

    return client


def test_schema_uses_runtime_introspection():
    client = make_client(
        {
            "dim_crop": "CREATE TABLE dim_crop (crop_id UInt64)",
            "fact_harvests": "CREATE TABLE fact_harvests (harvest_id UInt64)",
        },
    )

    markdown = load_schema_markdown(client, "urbangreen_dw")

    list_sql = client.query.call_args.args[0]

    assert "system.tables" in list_sql
    assert "name, create_table_query" in list_sql
    assert "{database:String}" in list_sql
    assert client.query.call_args.kwargs["parameters"] == {"database": "urbangreen_dw"}
    assert "## `dim_crop`" in markdown
    assert "## `fact_harvests`" in markdown
    client.query.assert_called_once()
    client.command.assert_not_called()


def test_schema_filters_materialized_view_inner_tables():
    client = make_client(
        {
            "events_mv": "CREATE MATERIALIZED VIEW events_mv AS SELECT 1",
        },
    )

    markdown = load_schema_markdown(client, "urbangreen_dw")
    list_sql = client.query.call_args.args[0]

    assert "NOT startsWith(name, '.inner')" in list_sql
    assert "events_mv" in markdown
    client.query.assert_called_once()
    client.command.assert_not_called()


def test_schema_renderer_is_a_pure_markdown_function():
    table_ddls = [
        ("dim_crop", "CREATE TABLE dim_crop (crop_id UInt64)"),
    ]

    first = render_schema_markdown("urbangreen_dw", table_ddls)
    second = render_schema_markdown("urbangreen_dw", table_ddls)

    assert first == second
    assert "Database: `urbangreen_dw`" in first
    assert "## `dim_crop`" in first
    assert "```sql\nCREATE TABLE dim_crop (crop_id UInt64)\n```" in first


def test_static_resources_match_bundled_markdown_docs():
    expected_metrics = (RESOURCE_DOCS_DIR / "metrics.md").read_text(encoding="utf-8")
    expected_conventions = (RESOURCE_DOCS_DIR / "conventions.md").read_text(encoding="utf-8")

    assert metrics_resource() == expected_metrics
    assert conventions_resource() == expected_conventions


def test_metrics_document_canonical_dashboard_metrics():
    markdown = metrics_resource()

    assert "Yield Efficiency" in markdown
    assert "SUM(total_yield_kg) / nullIf(MAX(size_m2), 0)" in markdown

    assert "Energy Efficiency" in markdown
    assert "SUM(energy_kwh) / nullIf(SUM(total_yield_kg), 0)" in markdown

    assert "Farm Expansion Progress" in markdown
    assert "COUNT(DISTINCT farm_id) / 100.0" in markdown

    assert "Waste Reduction Progress" in markdown
    assert "SUM(non_premium_yield_kg) / nullIf(SUM(total_yield_kg), 0)" in markdown

    assert "Environmental Compliance Rate" in markdown
    assert "SUM(in_range_count) / nullIf(SUM(reading_count), 0)" in markdown

    assert "Data Freshness" in markdown
    assert "dateDiff(" in markdown
    assert "max(reading_ts)" in markdown

    assert "one precomputed row per farm per day" in markdown
    assert "The leaderboard is the only exception" in markdown
    assert "Zero-yield farms" in markdown
    assert "do not rank `energy_efficiency_kwh_per_kg` independently" in markdown
    assert "farm_count - yield_rank + 1" in markdown
    assert "computed independently per `metric_date` using `rank()`" in markdown
    assert "`yield_rank`: `total_yield_kg` descending" in markdown
    assert "`quality_rank`: `premium_yield_share` descending" in markdown
    assert "`composite_rank`: `composite_score` descending" in markdown
    assert "following rank contains a gap" in markdown


def test_conventions_contain_examples():
    markdown = conventions_resource()

    assert "ReplacingMergeTree(_loaded_at)" in markdown
    assert "FROM urbangreen_dw.dim_crop FINAL" in markdown
    assert "argMax(name, _loaded_at)" in markdown
    assert "GROUP BY crop_id" in markdown
    assert "ReplacingMergeTree(_version)" in markdown
    assert "WHERE is_current = 1" in markdown
    assert "h.harvested_at >= f.valid_from" in markdown
    assert "h.harvested_at < f.valid_to" in markdown
    assert "FROM urbangreen_dw.fact_harvests FINAL" in markdown


def test_static_resource_sql_qualifies_warehouse_tables():
    markdown = metrics_resource() + conventions_resource()
    sql_blocks = re.findall(r"```sql\n(.*?)```", markdown, flags=re.DOTALL)
    table_references = [
        reference
        for sql in sql_blocks
        for reference in re.findall(r"\b(?:FROM|JOIN)\s+([A-Za-z_][\w.]*)", sql)
    ]

    assert table_references
    assert all(
        reference.startswith("urbangreen_dw.") or reference == "farm_history"
        for reference in table_references
    )
