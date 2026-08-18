"""
Unit tests for the slash-command prompt templates.

These assert contracts rather than wording. A template is prose that will be
reworded, so a test that pins a whole sentence fails on an edit that changed no
behaviour, and the suite ends up punishing editing instead of catching mistakes.
What cannot be reworded is asserted instead: the identifiers and table names the
model is sent to, the order two steps appear in, what a default renders to, and
the absence of something that must not come back.
"""

import inspect
import re

import pytest

from app import prompts
from app.prompts import analyze_metric, compare_farms, investigate_anomaly
from app.resources import CONVENTIONS_URI, METRICS_URI

PROMPTS = (analyze_metric, compare_farms, investigate_anomaly)

RENDERED = (
    analyze_metric("Energy Efficiency"),
    compare_farms([1, 2, 3]),
    investigate_anomaly(1, "Temperature"),
)

# Tables the ticket names that this warehouse does not have. The ticket predates
# the ETL work: there is no `agg_` prefix anywhere, so no hourly sensor
# aggregate either, and the readings table is plural.
PHANTOM_TABLES = ("agg_", "fact_sensor_reading ")


def order(rendered: str, *fragments: str) -> bool:
    """Report whether the fragments appear in the order given."""
    positions = [rendered.index(fragment) for fragment in fragments]
    return positions == sorted(positions)


# ---------------------------------------------------------------------------
# Shape
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prompt", PROMPTS)
def test_every_prompt_has_a_one_line_summary(prompt):
    """FastMCP shows the text above `Args:` in the slash-command picker, so it
    has to fit on one line."""
    summary = inspect.getdoc(prompt).split("Args:")[0].strip()

    assert summary
    assert len(summary.splitlines()) == 1


@pytest.mark.parametrize("prompt", PROMPTS)
def test_every_prompt_documents_each_argument(prompt):
    """The `Args:` entries become the argument descriptions clients display."""
    docstring = inspect.getdoc(prompt)

    for parameter in inspect.signature(prompt).parameters:
        assert f"{parameter}:" in docstring


@pytest.mark.parametrize("rendered", RENDERED)
def test_no_placeholder_survives_rendering(rendered):
    """An unfilled `{...}` would reach the model as literal text."""
    assert not re.search(r"\{[a-z_]+\}", rendered)


# ---------------------------------------------------------------------------
# Where the model is sent
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rendered", RENDERED)
def test_every_prompt_names_both_resources_before_the_query(rendered):
    """Reading the canonical definition after running the query would defeat the
    point of having one."""
    assert order(rendered, CONVENTIONS_URI, "execute_query")
    assert order(rendered, METRICS_URI, "execute_query")


@pytest.mark.parametrize("rendered", RENDERED)
def test_every_prompt_describes_a_table_before_it_queries(rendered):
    assert order(rendered, "describe_table", "execute_query")


@pytest.mark.parametrize("rendered", RENDERED)
def test_no_prompt_names_a_table_that_does_not_exist(rendered):
    for phantom in PHANTOM_TABLES:
        assert phantom not in rendered


def test_prompts_qualify_tables_with_the_module_wide_database(monkeypatch):
    """The database enters this module once, so a test can set it rather than
    read whatever the environment happens to hold."""
    monkeypatch.setattr(prompts, "WAREHOUSE", "some_other_db")

    assert "some_other_db.fact_daily_farm_metrics" in compare_farms([1])
    assert "some_other_db.fact_sensor_readings" in investigate_anomaly(1, "Temperature")


# ---------------------------------------------------------------------------
# Windowing
# ---------------------------------------------------------------------------


def test_the_day_count_reaches_every_template():
    assert "count 30 days back" in analyze_metric("Energy Efficiency")
    assert "count 90 days back" in analyze_metric("Energy Efficiency", days=90)
    assert "count 30 days back" in compare_farms([1])
    assert "count 7 days back" in investigate_anomaly(1, "Temperature")


@pytest.mark.parametrize("rendered", RENDERED)
def test_no_prompt_counts_back_from_the_clock(rendered):
    """The warehouse is batch-loaded, so a window measured from today can cover
    days that were never loaded."""
    assert "today()" not in rendered


@pytest.mark.parametrize("rendered", RENDERED)
def test_no_prompt_pins_a_date_column(rendered):
    """Each prompt lets the model choose between tables, so naming one table's
    date column would contradict that choice."""
    assert "metric_date >=" not in rendered
    assert "reading_date >=" not in rendered


# ---------------------------------------------------------------------------
# The contract of app.tools.execute_query
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rendered", RENDERED)
def test_every_prompt_names_the_payload_fields(rendered):
    """`execute_query` returns a dict instead of raising, and carries a
    truncation flag. Neither is any use if nothing tells the model to look."""
    assert "`error`" in rendered
    assert "`truncated: true`" in rendered


@pytest.mark.parametrize("rendered", RENDERED)
def test_every_prompt_separates_null_from_zero(rendered):
    """The canonical formulas divide with `nullIf`, so a NULL means there was
    nothing to measure. Reporting it as 0 states a measurement never taken."""
    assert "`NULL`" in rendered
    assert "`0`" in rendered


@pytest.mark.parametrize("rendered", RENDERED)
def test_every_prompt_closes_by_fencing_its_parameters(rendered):
    """The parameters are interpolated into a message the model reads as the
    user's own, so a value shaped like an instruction would carry the same
    standing as the workflow."""
    assert rendered.endswith(prompts._INPUT_GUARD)


# ---------------------------------------------------------------------------
# analyze_metric
# ---------------------------------------------------------------------------


def test_analyze_metric_carries_the_metric_and_asks_for_one_query():
    rendered = analyze_metric("Total Harvest Yield")

    assert "Total Harvest Yield" in rendered
    assert "execute_query once" in rendered
    assert "exploratory queries" in rendered


def test_analyze_metric_stops_when_the_metric_is_undefined():
    """An undefined metric has to stop the model, not start it improvising."""
    rendered = analyze_metric("Made Up Metric")

    assert order(rendered, METRICS_URI, "stop", "describe_table")


# ---------------------------------------------------------------------------
# compare_farms
# ---------------------------------------------------------------------------


def test_compare_farms_carries_the_requested_ids():
    assert "1, 2, 3" in compare_farms([1, 2, 3])


def test_compare_farms_without_ids_names_no_id():
    """The default has to widen the scope rather than render an empty list."""
    rendered = compare_farms([])

    assert not re.search(r"farms \d", rendered)
    assert rendered != compare_farms([1])


def test_compare_farms_prefers_the_leaderboard_over_the_rollup():
    """Re-ranking from the daily metrics produces an order that disagrees with
    the dashboard as soon as the set of farms differs, so the stored ranks are
    offered first."""
    rendered = compare_farms([1, 2])

    assert order(rendered, "fact_farm_leaderboard", "fact_daily_farm_metrics")


def test_compare_farms_resolves_names_from_the_current_dimension():
    rendered = compare_farms([1, 2, 3])

    assert "dim_farm FINAL" in rendered
    assert "is_current = 1" in rendered
    assert "bare farm id" in rendered


def test_compare_farms_excludes_an_unmeasured_farm_from_the_ranking():
    """A farm with no rows in the window has not performed badly; it has not
    been measured. Sorting it last would state a result nobody produced."""
    rendered = compare_farms([1, 2])

    assert "not last in it" in rendered


def test_compare_farms_names_no_metric_specific_direction():
    """Which end of the scale wins is a fact about the metric and lives in the
    metrics resource. An example here would be a second copy of it."""
    rendered = compare_farms([1, 2], dimension="energy efficiency")

    assert "for energy efficiency, lower is better" not in rendered
    assert "higher or lower is better" in rendered


# ---------------------------------------------------------------------------
# investigate_anomaly
# ---------------------------------------------------------------------------


def test_investigate_anomaly_carries_the_farm_and_sensor_type():
    rendered = investigate_anomaly(1, "CO2 Concentration")

    assert "CO2 Concentration" in rendered
    assert "farm_id = 1" in rendered


def test_investigate_anomaly_counts_from_the_stored_flag():
    """`is_anomaly` was set against the range valid at reading time, and the
    sensor type is versioned, so recomputing it changes historical answers."""
    rendered = investigate_anomaly(1, "Temperature")

    assert "is_anomaly" in rendered
    assert order(rendered, "is_anomaly", "optimal_min", "optimal_max")


def test_investigate_anomaly_points_at_the_canonical_rate_by_name():
    """The rate is defined in the metrics resource. Writing the ratio out here
    would be a second copy that drifts the moment the definition changes."""
    rendered = investigate_anomaly(1, "Temperature")

    assert '"Sensor anomaly rate"' in rendered
    assert "ratio out from memory" in rendered
    assert "anomaly_count / reading_count" not in rendered


def test_investigate_anomaly_separates_no_anomalies_from_no_readings():
    """Both come back as an empty trend, and only one of them means the sensor
    is healthy."""
    rendered = investigate_anomaly(1, "Temperature")

    assert order(rendered, "no anomaly was found", "reported nothing in that window")


def test_investigate_anomaly_reads_the_rollup_before_the_atomic_table():
    """The rollup carries the rate and the daily extremes, so the largest table
    in the warehouse is only reached for individual readings."""
    rendered = investigate_anomaly(2, "pH Level")

    assert order(
        rendered,
        "fact_daily_sensor_metrics",
        "anomaly_count",
        "min_value and max_value",
        "fact_sensor_readings FINAL",
    )
