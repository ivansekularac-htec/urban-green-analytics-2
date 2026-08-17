"""Tests for the Markdown knowledge resources."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.resources import (
    conventions_resource,
    load_schema_markdown,
    metrics_resource,
    render_schema_markdown,
    schema_resource,
)


def make_client(
    table_names: list[str],
    ddl_by_table: dict[str, str],
) -> MagicMock:
    client = MagicMock()

    client.query.return_value = SimpleNamespace(
        result_rows=[(name,) for name in table_names]
    )

    client.command.side_effect = lambda sql: next(
        ddl
        for table_name, ddl in ddl_by_table.items()
        if f"`{table_name}`" in sql
    )

    return client


def test_schema_uses_runtime_introspection():
    client = make_client(
        ["dim_crop", "fact_harvests"],
        {
            "dim_crop": "CREATE TABLE dim_crop (crop_id UInt64)",
            "fact_harvests": "CREATE TABLE fact_harvests (harvest_id UInt64)",
        },
    )

    markdown = load_schema_markdown(client, "urbangreen_dw")

    list_sql = client.query.call_args.args[0]

    assert "system.tables" in list_sql
    assert "{database:String}" in list_sql
    assert client.query.call_args.kwargs["parameters"] == {"database": "urbangreen_dw"}
    assert client.command.call_args_list[0].args[0] == (
        "SHOW CREATE TABLE `urbangreen_dw`.`dim_crop`"
    )
    assert client.command.call_args_list[1].args[0] == (
        "SHOW CREATE TABLE `urbangreen_dw`.`fact_harvests`"
    )
    assert "## `dim_crop`" in markdown
    assert "## `fact_harvests`" in markdown


def test_schema_filters_materialized_view_inner_tables():
    client = make_client(
        [".inner_id.123", ".inner.events_mv", "events_mv"],
        {
            "events_mv": "CREATE MATERIALIZED VIEW events_mv AS SELECT 1",
        },
    )

    markdown = load_schema_markdown(client, "urbangreen_dw")

    assert ".inner_id.123" not in markdown
    assert ".inner.events_mv" not in markdown
    assert "events_mv" in markdown
    client.command.assert_called_once()


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


def test_schema_is_lazy_and_cached():
    client = make_client(
        ["dim_crop"],
        {
            "dim_crop": "CREATE TABLE dim_crop (crop_id UInt64)",
        },
    )
    settings = SimpleNamespace(clickhouse_db="urbangreen_dw")

    schema_resource.cache_clear()

    with (
        patch("app.resources.get_client", return_value=client) as get_client,
        patch("app.resources.get_settings", return_value=settings) as get_settings,
    ):
        first = schema_resource()
        second = schema_resource()

    assert first == second
    get_client.assert_called_once_with()
    get_settings.assert_called_once_with()
    client.query.assert_called_once()
    client.command.assert_called_once()

    schema_resource.cache_clear()


def test_metrics_document_grains_and_formulas():
    markdown = metrics_resource()

    assert "one row per farm per day" in markdown
    assert "one row per farm and sensor type per day" in markdown
    assert "`total_yield_kg`" in markdown
    assert "sum(sum_value) / sum(reading_count)" in markdown
    assert "premium_yield_kg / total_yield_kg" in markdown
    assert "energy_kwh / total_yield_kg" in markdown


def test_conventions_contain_examples():
    markdown = conventions_resource()

    assert "ReplacingMergeTree(_loaded_at)" in markdown
    assert "FROM dim_crop FINAL" in markdown
    assert "argMax(name, _loaded_at)" in markdown
    assert "GROUP BY crop_id" in markdown
    assert "ReplacingMergeTree(_version)" in markdown
    assert "WHERE is_current = 1" in markdown
    assert "h.harvested_at >= f.valid_from" in markdown
    assert "h.harvested_at < f.valid_to" in markdown
    assert "FROM fact_harvests FINAL" in markdown
