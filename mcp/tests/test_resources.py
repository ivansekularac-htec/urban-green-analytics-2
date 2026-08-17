"""
Unit tests for the static knowledge resources.

Covers schema introspection, filtering of materialized-view inner tables,
process-lifetime caching, failure handling, and the content of the metric and
convention documents - including that the conventions stay limited to rules the
DDL cannot carry as a table or column COMMENT.
"""

from unittest.mock import MagicMock

from clickhouse_connect.driver.exceptions import DatabaseError

from app.resources import (
    INTERNAL_TABLE_PREFIX,
    SCHEMA_DATABASE,
    _load_schema,
    render_conventions,
    render_metrics,
    render_schema,
)

DIM_FARM_DDL = "CREATE TABLE urbangreen_dw.dim_farm (farm_id UInt64) ENGINE = ReplacingMergeTree"
FACT_HARVESTS_DDL = (
    "CREATE TABLE urbangreen_dw.fact_harvests (harvest_id UInt64) ENGINE = ReplacingMergeTree"
)


def _client(result_rows) -> MagicMock:
    client = MagicMock()
    result = MagicMock()
    result.result_rows = list(result_rows)
    client.query.return_value = result
    return client


# ---------------------------------------------------------------------------
# render_schema
# ---------------------------------------------------------------------------


def test_render_schema_lists_every_table_with_its_ddl():
    _load_schema.cache_clear()
    client = _client(
        [
            ("dim_farm", DIM_FARM_DDL),
            ("fact_harvests", FACT_HARVESTS_DDL),
        ]
    )

    schema = render_schema(client)

    assert "# Warehouse schema" in schema
    assert "## dim_farm" in schema
    assert "## fact_harvests" in schema
    assert DIM_FARM_DDL in schema
    assert FACT_HARVESTS_DDL in schema

    _load_schema.cache_clear()


def test_render_schema_binds_the_database_as_a_parameter():
    _load_schema.cache_clear()
    client = _client([])

    render_schema(client)

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "{database:String}" in sql
    assert parameters == {
        "database": SCHEMA_DATABASE,
        "internal_prefix": INTERNAL_TABLE_PREFIX,
    }
    assert SCHEMA_DATABASE not in sql

    _load_schema.cache_clear()


def test_render_schema_excludes_materialized_view_inner_tables():
    """The `.inner` tables behind a materialized view are an implementation
    detail and must not reach the model."""
    _load_schema.cache_clear()
    client = _client([("dim_farm", DIM_FARM_DDL)])

    render_schema(client)

    sql = client.query.call_args.args[0]
    parameters = client.query.call_args.kwargs["parameters"]

    assert "NOT startsWith(name, {internal_prefix:String})" in sql
    assert parameters["internal_prefix"] == INTERNAL_TABLE_PREFIX
    assert INTERNAL_TABLE_PREFIX not in sql

    _load_schema.cache_clear()


def test_render_schema_is_built_once_and_cached():
    """The warehouse schema is static while the stack is up, so the second
    read must not hit ClickHouse again."""
    _load_schema.cache_clear()
    client = _client([("dim_farm", DIM_FARM_DDL)])

    first = render_schema(client)
    second = render_schema(client)

    assert first == second
    client.query.assert_called_once()

    _load_schema.cache_clear()


def test_render_schema_reports_a_failure_as_markdown():
    _load_schema.cache_clear()
    client = MagicMock()
    client.query.side_effect = DatabaseError("Connection refused")

    schema = render_schema(client)

    assert schema.startswith("# Warehouse schema")
    assert "could not be read" in schema
    assert "Connection refused" in schema

    _load_schema.cache_clear()


def test_render_schema_retries_after_a_failure():
    """A failure must not be cached: the next read has to try again, otherwise
    one blip would leave the resource broken until the process restarts."""
    _load_schema.cache_clear()
    client = MagicMock()
    failure = MagicMock()
    failure.result_rows = []
    client.query.side_effect = [
        DatabaseError("Connection refused"),
        _client([("dim_farm", DIM_FARM_DDL)]).query.return_value,
    ]

    failed = render_schema(client)
    recovered = render_schema(client)

    assert "could not be read" in failed
    assert "## dim_farm" in recovered
    assert client.query.call_count == 2

    _load_schema.cache_clear()


# ---------------------------------------------------------------------------
# render_metrics
# ---------------------------------------------------------------------------


def test_render_metrics_returns_the_metric_document():
    metrics = render_metrics()

    assert metrics.startswith("# Canonical metric definitions")
    assert "```sql" in metrics


def test_render_metrics_defines_the_dashboard_metrics():
    metrics = render_metrics()

    for heading in (
        "Total harvest yield",
        "Energy efficiency",
        "Premium yield share",
        "Environmental compliance rate",
        "Farm leaderboard",
    ):
        assert heading in metrics


def test_render_metrics_uses_the_re_aggregation_safe_average():
    """The daily rollups store sums, so the documented average must divide sums
    rather than average the daily averages."""
    metrics = render_metrics()

    assert "sum(sum_value) / nullIf(sum(reading_count), 0)" in metrics


# ---------------------------------------------------------------------------
# render_conventions
# ---------------------------------------------------------------------------


def test_render_conventions_returns_the_conventions_document():
    conventions = render_conventions()

    assert conventions.startswith("# Query conventions")
    assert "```sql" in conventions


def test_render_conventions_covers_the_cross_table_rules():
    """What is left after the per-object facts moved into the DDL: joins and
    query shapes that span more than one table."""
    conventions = render_conventions()

    assert "valid_from" in conventions
    assert "valid_to" in conventions
    assert "is_current" in conventions
    assert "argMax" in conventions


def test_render_conventions_defers_per_table_facts_to_the_ddl():
    """Engine and column facts belong in each object's COMMENT, where they
    cannot drift from the table they describe. Restating them here would
    reintroduce the duplication this document exists to avoid."""
    conventions = render_conventions()

    assert "MergeTree" not in conventions
    assert "sum_value" not in conventions
    assert "is_anomaly" not in conventions


def test_render_conventions_explains_the_key_and_id_distinction():
    conventions = render_conventions()

    assert "`*_key` is a surrogate" in conventions
    assert "date_key" in conventions
