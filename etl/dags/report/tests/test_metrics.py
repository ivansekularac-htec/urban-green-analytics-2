"""Tests for the fixed KPI queries.

These assert the contract the queries must keep - which table each figure reads,
that ratios divide with nullIf, that active farms comes from the dimension and
the leaderboard is read - rather than the exact wording of the SQL.
"""

from report import metrics
from report.tests.conftest import FakeResult, FakeWarehouse


def test_active_farms_reads_the_dimension_not_the_fact_table():
    """A farm with no activity that day is still active, so the count comes from
    dim_farm, never from counting fact rows."""
    assert "dim_farm" in metrics._ACTIVE_FARMS_SQL
    assert "is_current = 1" in metrics._ACTIVE_FARMS_SQL
    assert "fact_daily_farm_metrics" not in metrics._ACTIVE_FARMS_SQL


def test_totals_read_the_daily_fact_table_with_final_and_nullif():
    sql = metrics._TOTALS_SQL
    assert "fact_daily_farm_metrics FINAL" in sql
    # Ratios divide with nullIf, and the sums are pre-aggregated in a subquery so
    # no aggregate is aliased to a column it sums (which ClickHouse rejects).
    assert "nullIf(yield_kg, 0)" in sql
    assert "nullIf(readings, 0)" in sql
    assert "SUM(total_yield_kg)" in sql
    # The alias never equals the summed column, so a later reference cannot
    # resolve to SUM(SUM(...)).
    assert "SUM(total_yield_kg) AS total_yield_kg" not in sql


def test_top_farms_read_the_precomputed_leaderboard_rank():
    sql = metrics._TOP_FARMS_SQL
    assert "fact_farm_leaderboard AS l FINAL" in sql
    assert "l.composite_rank" in sql
    # The alias goes before FINAL, the order ClickHouse parses.
    assert "AS d FINAL" in sql


def test_sensors_read_the_daily_sensor_table_by_type():
    sql = metrics._SENSORS_SQL
    assert "fact_daily_sensor_metrics FINAL" in sql
    assert "dim_sensor_type AS d FINAL" in sql
    assert "GROUP BY sensor_type_id" in sql


def test_fetch_kpis_marks_an_empty_day():
    warehouse = FakeWarehouse(
        [
            FakeResult(["total_yield_kg"], []),  # totals: no row
            FakeResult(["active_farms"], [(75,)]),
            FakeResult(["rank", "farm"], []),  # no leaderboard rows
            FakeResult(["sensor_type", "unit", "readings", "anomalies"], []),
        ]
    )

    kpis = metrics.fetch_kpis(warehouse, "2026-01-01")

    assert kpis["has_data"] is False
    assert kpis["active_farms"] == 75
    assert kpis["sensors"] == []


def test_fetch_kpis_passes_the_date_as_a_bound_parameter():
    warehouse = FakeWarehouse(
        [
            FakeResult(["total_yield_kg"], [(100.0,)]),
            FakeResult(["active_farms"], [(75,)]),
            FakeResult(["rank"], [(1,)]),
            FakeResult(
                ["sensor_type", "unit", "readings", "anomalies"], [("pH", "pH", 300, 1)]
            ),
        ]
    )

    kpis = metrics.fetch_kpis(warehouse, "2026-08-15")

    totals_sql, totals_params = warehouse.queries[0]
    assert totals_params == {"report_date": "2026-08-15"}
    assert "{report_date:Date}" in totals_sql
    assert kpis["sensors"] == [
        {"sensor_type": "pH", "unit": "pH", "readings": 300, "anomalies": 1}
    ]
