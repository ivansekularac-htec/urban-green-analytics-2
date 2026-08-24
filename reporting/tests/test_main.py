"""Tests for the reporting pipeline entry point."""

from datetime import date
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.main import main, resolve_day, run_report

DAY = date(2026, 8, 15)

STATE = {
    "summary": {"source": "qwen3.5:2b"},
    "published": {
        "key": "reports/executive/date=2026-08-15/report.html",
        "stored": True,
        "emailed": True,
        "warnings": [],
    },
}


def test_a_run_reports_what_was_published():
    with patch("app.main.graph.run", return_value=STATE) as run:
        result = run_report("2026-08-15")

    run.assert_called_once_with(DAY)
    assert result == {
        "day": "2026-08-15",
        "key": "reports/executive/date=2026-08-15/report.html",
        "stored": True,
        "emailed": True,
        "summary_source": "qwen3.5:2b",
        "warnings": [],
    }


def test_an_unreadable_day_is_rejected():
    # The caller is the DAG, so this has to raise rather than report a
    # published key for a day nobody asked for.
    with pytest.raises(ValueError):
        run_report("not-a-date")


def test_latest_resolves_to_the_newest_loaded_day():
    with (
        patch("app.main.metrics.get_client"),
        patch("app.main.metrics.latest_date", return_value=DAY),
    ):
        assert resolve_day("latest") == DAY


def test_latest_fails_when_the_warehouse_is_empty():
    with (
        patch("app.main.metrics.get_client"),
        patch("app.main.metrics.latest_date", return_value=None),
        pytest.raises(ValueError),
    ):
        resolve_day("latest")


def test_the_cli_runs_the_day_it_is_given():
    with (
        patch("sys.argv", ["main", "--date", "2026-08-15"]),
        patch("app.main.get_settings", return_value=SimpleNamespace(log_level="INFO")),
        patch("app.main.graph.run", return_value=STATE) as run,
    ):
        main()

    run.assert_called_once_with(DAY)


def test_the_cli_defaults_to_the_newest_loaded_day():
    with (
        patch("sys.argv", ["main"]),
        patch("app.main.get_settings", return_value=SimpleNamespace(log_level="INFO")),
        patch("app.main.metrics.get_client"),
        patch("app.main.metrics.latest_date", return_value=DAY),
        patch("app.main.graph.run", return_value=STATE) as run,
    ):
        main()

    run.assert_called_once_with(DAY)
