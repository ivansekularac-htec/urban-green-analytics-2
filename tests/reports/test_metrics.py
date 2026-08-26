"""Tests for fixed, date-bound executive KPI retrieval."""

from datetime import date
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from reports import metrics

REPORT_DATE = date(2026, 8, 15)


def result(rows: list[dict]) -> SimpleNamespace:
    return SimpleNamespace(named_results=lambda: iter(rows))


def kpi_row(**overrides) -> dict:
    values = {
        "source_row_count": 3,
        "farms_reporting": 3,
        "total_yield_kg": Decimal("1200.500"),
        "harvest_count": 42,
        "premium_yield_kg": Decimal("300.125"),
        "energy_kwh": 2400.0,
        "reading_count": 5000,
        "anomaly_count": 125,
    }
    values.update(overrides)
    return values


def top_farm_row() -> dict:
    return {
        "rank": 1,
        "farm_name": "Riverside Farm",
        "total_yield_kg": Decimal("500.000"),
        "premium_yield_share": 0.45,
        "energy_efficiency_kwh_per_kg": 1.8,
        "composite_score": 9.5,
    }


def run_retrieval(row=None, leaderboard=None):
    client = MagicMock()
    client.query.side_effect = [
        result([kpi_row() if row is None else row]),
        result([top_farm_row()] if leaderboard is None else leaderboard),
    ]
    with patch("reports.metrics.get_client", return_value=client):
        output = metrics.retrieve_metrics({"report_date": REPORT_DATE})
    return output, client


def test_retrieval_returns_normalized_kpis_and_precomputed_leaderboard():
    output, client = run_retrieval()

    assert output["metrics"]["total_yield_kg"] == 1200.5
    assert output["metrics"]["premium_yield_share"] == pytest.approx(300.125 / 1200.5)
    assert output["metrics"]["anomaly_rate"] == 0.025
    assert output["top_farms"][0]["farm_name"] == "Riverside Farm"
    assert client.close.call_count == 1


def test_every_query_binds_the_report_date():
    _, client = run_retrieval()

    for query_call in client.query.call_args_list:
        assert query_call.kwargs["parameters"] == {"report_date": REPORT_DATE}
        assert REPORT_DATE.isoformat() not in query_call.args[0]


def test_queries_use_aggregate_tables_and_historical_farm_key():
    assert "fact_daily_farm_metrics" in metrics.EXECUTIVE_KPI_SQL
    assert "fact_farm_leaderboard" in metrics.TOP_FARMS_SQL
    assert "farm.farm_key = leaderboard.farm_key" in metrics.TOP_FARMS_SQL
    assert "fact_harvests" not in metrics.EXECUTIVE_KPI_SQL
    assert "fact_sensor_readings" not in metrics.EXECUTIVE_KPI_SQL


def test_zero_denominators_are_not_reported_as_zero_ratios():
    output, _ = run_retrieval(
        kpi_row(
            total_yield_kg=Decimal("0"),
            premium_yield_kg=Decimal("0"),
            reading_count=0,
            anomaly_count=0,
        )
    )

    assert output["metrics"]["premium_yield_share"] is None
    assert output["metrics"]["energy_efficiency_kwh_per_kg"] is None
    assert output["metrics"]["anomaly_rate"] is None


def test_missing_daily_rows_fail_clearly_and_close_the_client():
    client = MagicMock()
    client.query.side_effect = [
        result([kpi_row(source_row_count=0)]),
        result([]),
    ]

    with (
        patch("reports.metrics.get_client", return_value=client),
        pytest.raises(ValueError, match=str(REPORT_DATE)),
    ):
        metrics.retrieve_metrics({"report_date": REPORT_DATE})

    client.close.assert_called_once()
