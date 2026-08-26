"""Tests for daily executive report DAG scheduling and invocation."""

from datetime import date
from unittest.mock import patch

import pendulum

from etl.dags import daily_executive_report as dag_module


def test_dag_schedule_and_concurrency_match_cluster_limits():
    dag = dag_module.daily_executive_report_dag

    assert dag.catchup is False
    assert dag.max_active_runs == 1
    assert dag.max_active_tasks == 1
    assert dag.timetable.expression == "0 6 * * *"
    assert len(dag.tasks) == 1

    task = dag.get_task("build_and_publish_report")
    assert task.retries == 2


def test_task_uses_logical_date_and_returns_object_key():
    task = dag_module.daily_executive_report_dag.get_task("build_and_publish_report")
    expected_key = "reports/executive/date=2026-08-15/report.html"
    context = {"logical_date": pendulum.datetime(2026, 8, 15, 6, 0, tz="UTC")}

    with (
        patch("etl.dags.daily_executive_report.get_current_context", return_value=context),
        patch(
            "etl.dags.daily_executive_report.run_report",
            return_value={
                "published_bucket": "staging",
                "object_key": expected_key,
            },
        ) as run_report,
    ):
        result = task.python_callable()

    run_report.assert_called_once_with(date(2026, 8, 15))
    assert result == expected_key
