"""Tests for reading the day's KPIs from the warehouse."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

from app import metrics

DAY = date(2026, 8, 19)


def result(rows: list[dict]) -> SimpleNamespace:
    """Stand in for a clickhouse-connect result."""

    return SimpleNamespace(named_results=lambda: iter(rows))


def client_returning(*results) -> MagicMock:
    client = MagicMock()
    client.query.side_effect = list(results)

    return client


def totals(**overrides) -> dict:
    row = {
        "yield_kg": Decimal("1200.500"),
        "harvests": 42,
        "energy_kwh": 2400.0,
        "readings": 5000,
        "anomalies": 150,
    }
    row.update(overrides)

    return row


def collect(totals_row=None, farms=15, sensors=None, leaderboard=None) -> dict:
    client = client_returning(
        result([totals_row if totals_row is not None else totals()]),
        result([{"farms": farms}]),
        result(sensors if sensors is not None else []),
        result(leaderboard if leaderboard is not None else []),
    )

    return metrics.collect(client, DAY)


def test_latest_date_returns_the_newest_loaded_day():
    client = client_returning(result([{"latest": DAY}]))

    assert metrics.latest_date(client) == DAY


def test_latest_date_is_none_when_nothing_is_loaded():
    # max() over an empty table answers with the epoch, not with no row.
    client = client_returning(result([{"latest": date(1970, 1, 1)}]))

    assert metrics.latest_date(client) is None


def test_collect_returns_the_days_totals_as_floats():
    collected = collect()

    assert collected["day"] == DAY
    assert collected["totals"]["yield_kg"] == 1200.5
    assert collected["totals"]["farms"] == 15


def test_collect_derives_the_ratios():
    collected = collect()

    assert collected["totals"]["energy_per_kg"] == 2400.0 / 1200.5
    assert collected["totals"]["anomaly_rate"] == 150 / 5000


def test_a_ratio_with_no_denominator_is_none_not_zero():
    # A day with no harvest was not perfectly efficient, it was not measured.
    collected = collect(totals(yield_kg=Decimal("0.000"), readings=0))

    assert collected["totals"]["energy_per_kg"] is None
    assert collected["totals"]["anomaly_rate"] is None


def test_active_farms_comes_from_the_dimension_not_the_fact_rollup():
    # A farm with no harvest and no reading that day is still an active farm.
    collected = collect(farms=75)

    assert collected["totals"]["farms"] == 75


def test_collect_returns_the_sensor_and_leaderboard_breakdowns():
    collected = collect(
        sensors=[{"sensor_type": "Temperature", "unit": "C", "readings": 100, "anomalies": 9}],
        leaderboard=[{"farm": "Riverside", "yield_kg": Decimal("500.000"), "rank": 1}],
    )

    assert collected["sensors"][0]["sensor_type"] == "Temperature"
    assert collected["leaderboard"][0]["farm"] == "Riverside"
    assert collected["leaderboard"][0]["yield_kg"] == 500.0


def test_collect_binds_the_day_rather_than_formatting_it():
    client = client_returning(result([totals()]), result([{"farms": 15}]), result([]), result([]))

    metrics.collect(client, DAY)

    for call in client.query.call_args_list:
        assert call.kwargs["parameters"] == {"day": DAY}
        assert "2026-08-19" not in call.args[0]
