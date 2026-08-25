"""Tests for executive KPI retrieval."""

import os
from datetime import date
from decimal import Decimal
from unittest import TestCase
from unittest.mock import MagicMock, patch

from report.metrics import (
    _get_clickhouse_client,
    retrieve_metrics,
)


class RetrieveMetricsTests(TestCase):
    def test_clickhouse_client_uses_airflow_connection_in_task(self):
        connection = MagicMock()
        connection.host = "urbangreen-clickhouse"
        connection.port = 8123
        connection.login = "urbangreen"
        connection.password = "secret"
        connection.schema = "urbangreen_dw"

        connections = MagicMock()
        connections.get.return_value = connection

        with (
            patch(
                "report.metrics.get_current_context",
                return_value={"conn": connections},
            ),
            patch("report.metrics.clickhouse_connect.get_client") as get_client,
        ):
            _get_clickhouse_client()

        connections.get.assert_called_once_with("urbangreen_clickhouse")

        get_client.assert_called_once_with(
            host="urbangreen-clickhouse",
            port=8123,
            username="urbangreen",
            password="secret",
            database="urbangreen_dw",
        )

    def test_clickhouse_client_uses_environment_standalone(self):
        with (
            patch(
                "report.metrics.get_current_context",
                side_effect=RuntimeError,
            ),
            patch.dict(
                os.environ,
                {
                    "CLICKHOUSE_HOST": "urbangreen-clickhouse",
                    "CLICKHOUSE_HTTP_PORT": "8123",
                    "CLICKHOUSE_USER": "urbangreen",
                    "CLICKHOUSE_PASSWORD": "secret",
                    "CLICKHOUSE_DB": "urbangreen_dw",
                },
            ),
            patch("report.metrics.clickhouse_connect.get_client") as get_client,
        ):
            _get_clickhouse_client()

        get_client.assert_called_once_with(
            host="urbangreen-clickhouse",
            port=8123,
            username="urbangreen",
            password="secret",
            database="urbangreen_dw",
        )

    def test_retrieve_metrics_returns_report_data(self):
        client = MagicMock()

        metrics_result = MagicMock()
        metrics_result.column_names = (
            "source_rows",
            "reporting_farms",
            "total_harvest_yield_kg",
            "total_energy_kwh",
            "energy_efficiency_kwh_per_kg",
            "waste_reduction_progress",
            "environmental_compliance_rate",
            "sensor_anomaly_rate",
            "total_sensor_readings",
        )
        metrics_result.result_rows = [
            (
                75,
                75,
                Decimal("1200.5"),
                Decimal("2400.0"),
                Decimal("1.9992"),
                Decimal("0.15"),
                Decimal("0.92"),
                Decimal("0.02"),
                18040,
            )
        ]

        top_farms_result = MagicMock()
        top_farms_result.column_names = (
            "rank",
            "farm",
            "city",
            "total_yield_kg",
            "premium_yield_share",
            "energy_efficiency_kwh_per_kg",
        )
        top_farms_result.result_rows = [
            (
                1,
                "UG Farm 01",
                "Cologne",
                Decimal("250.5"),
                Decimal("0.45"),
                Decimal("1.80"),
            ),
            (
                2,
                "UG Farm 02",
                "Munich",
                Decimal("220.0"),
                Decimal("0.40"),
                Decimal("2.10"),
            ),
        ]

        sensors_result = MagicMock()
        sensors_result.column_names = (
            "sensor_type",
            "unit",
            "readings",
            "anomalies",
            "anomaly_rate",
            "compliance_rate",
        )
        sensors_result.result_rows = [
            (
                "Temperature",
                "°C",
                3000,
                30,
                Decimal("0.01"),
                Decimal("0.95"),
            ),
            (
                "Humidity",
                "%",
                3000,
                15,
                Decimal("0.005"),
                Decimal("0.97"),
            ),
        ]

        client.query.side_effect = [
            metrics_result,
            top_farms_result,
            sensors_result,
        ]

        with patch("report.metrics._get_clickhouse_client", return_value=client):
            response = retrieve_metrics({"report_date": "2026-08-20"})

        self.assertEqual(
            response,
            {
                "metrics": {
                    "reporting_farms": 75,
                    "total_harvest_yield_kg": 1200.5,
                    "total_energy_kwh": 2400.0,
                    "energy_efficiency_kwh_per_kg": 1.9992,
                    "waste_reduction_progress": 0.15,
                    "environmental_compliance_rate": 0.92,
                    "sensor_anomaly_rate": 0.02,
                    "total_sensor_readings": 18040,
                },
                "top_farms": [
                    {
                        "rank": 1,
                        "farm": "UG Farm 01",
                        "city": "Cologne",
                        "total_yield_kg": 250.5,
                        "premium_yield_share": 0.45,
                        "energy_efficiency_kwh_per_kg": 1.8,
                    },
                    {
                        "rank": 2,
                        "farm": "UG Farm 02",
                        "city": "Munich",
                        "total_yield_kg": 220.0,
                        "premium_yield_share": 0.4,
                        "energy_efficiency_kwh_per_kg": 2.1,
                    },
                ],
                "sensors": [
                    {
                        "sensor_type": "Temperature",
                        "unit": "°C",
                        "readings": 3000,
                        "anomalies": 30,
                        "anomaly_rate": 0.01,
                        "compliance_rate": 0.95,
                    },
                    {
                        "sensor_type": "Humidity",
                        "unit": "%",
                        "readings": 3000,
                        "anomalies": 15,
                        "anomaly_rate": 0.005,
                        "compliance_rate": 0.97,
                    },
                ],
            },
        )

        self.assertEqual(client.query.call_count, 3)

        metrics_query = client.query.call_args_list[0].args[0]
        metrics_parameters = client.query.call_args_list[0].kwargs["parameters"]

        self.assertIn("urbangreen_dw.fact_daily_farm_metrics FINAL", metrics_query)
        self.assertIn("urbangreen_dw.fact_daily_sensor_metrics FINAL", metrics_query)
        self.assertIn("sum(reading_count) AS total_sensor_readings", metrics_query)
        self.assertEqual(
            metrics_parameters,
            {"report_date": date(2026, 8, 20)},
        )

        top_farms_query = client.query.call_args_list[1].args[0]
        top_farms_parameters = client.query.call_args_list[1].kwargs["parameters"]

        self.assertIn("urbangreen_dw.fact_farm_leaderboard FINAL", top_farms_query)
        self.assertIn("urbangreen_dw.dim_farm FINAL", top_farms_query)
        self.assertEqual(
            top_farms_parameters,
            {"report_date": date(2026, 8, 20), "top_n": 5},
        )

        sensors_query = client.query.call_args_list[2].args[0]
        sensors_parameters = client.query.call_args_list[2].kwargs["parameters"]

        self.assertIn("urbangreen_dw.fact_daily_sensor_metrics FINAL", sensors_query)
        self.assertIn("urbangreen_dw.dim_sensor_type FINAL", sensors_query)
        self.assertIn("sensor_type_id", sensors_query)
        self.assertEqual(
            sensors_parameters,
            {"report_date": date(2026, 8, 20)},
        )

        client.close.assert_called_once()

    def test_retrieve_metrics_rejects_date_without_data(self):
        client = MagicMock()

        result = MagicMock()
        result.result_rows = [
            (
                0,
                0,
                None,
                None,
                None,
                None,
                None,
                None,
                None,
            )
        ]

        client.query.return_value = result

        with patch(
            "report.metrics._get_clickhouse_client",
            return_value=client,
        ):
            with self.assertRaisesRegex(ValueError, "No daily farm metrics found"):
                retrieve_metrics({"report_date": "2026-08-20"})

        self.assertEqual(client.query.call_count, 1)
        client.close.assert_called_once()

    def test_retrieve_metrics_rejects_invalid_date(self):
        with patch("report.metrics._get_clickhouse_client") as get_client:
            with self.assertRaises(ValueError):
                retrieve_metrics({"report_date": "invalid-date"})

        get_client.assert_not_called()
