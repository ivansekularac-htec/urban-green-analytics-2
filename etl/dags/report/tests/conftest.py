"""Test setup for the report package.

The package lives under `etl/dags/` so Airflow can import it as `report`. The
same import path is put on `sys.path` here, so the tests import it the way the
DAG does.
"""

import sys
from pathlib import Path

import pytest

# etl/dags, two levels up from this file (report/tests/conftest.py).
_DAGS_DIR = str(Path(__file__).resolve().parents[2])
if _DAGS_DIR not in sys.path:
    sys.path.insert(0, _DAGS_DIR)

from report.deps import EmailConfig, OllamaConfig, ReportDeps  # noqa: E402


class FakeResult:
    """A stand-in for a clickhouse-connect query result."""

    def __init__(self, column_names, result_rows):
        self.column_names = column_names
        self.result_rows = result_rows


class FakeWarehouse:
    """Returns queued results in order and records the SQL it was asked."""

    def __init__(self, results):
        self._results = list(results)
        self.queries = []

    def query(self, sql, parameters=None):
        self.queries.append((sql, parameters or {}))
        return self._results.pop(0)


class FakeS3:
    """Records every put_object call, so a test can assert the key and body."""

    def __init__(self):
        self.puts = []

    def put_object(self, **kwargs):
        self.puts.append(kwargs)


@pytest.fixture
def sample_kpis():
    return {
        "report_date": "2026-08-15",
        "has_data": True,
        "totals": {
            "total_yield_kg": 1234.5,
            "total_energy_kwh": 8900.0,
            "energy_efficiency_kwh_per_kg": 7.21,
            "non_premium_share": 0.34,
            "compliance_rate": 0.97,
            "anomaly_rate": 0.03,
            "farms_reporting": 70,
        },
        "active_farms": 75,
        "top_farms": [
            {
                "rank": 1,
                "farm": "UG Farm 043",
                "city": "Berlin",
                "total_yield_kg": 31.824,
                "premium_yield_share": 0.585,
                "energy_efficiency_kwh_per_kg": 5.1,
            }
        ],
    }


@pytest.fixture
def deps():
    return ReportDeps(
        warehouse=FakeWarehouse([]),
        s3=FakeS3(),
        bucket="staging",
        ollama=OllamaConfig(
            host="ollama:11434", model="test-model", num_predict=200, timeout_seconds=30
        ),
        email=EmailConfig(
            host="mailpit", port=1025, sender="from@x.local", recipient="to@x.local"
        ),
    )
