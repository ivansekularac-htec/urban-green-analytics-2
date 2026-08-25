"""Tests for executive report HTML rendering."""

from unittest import TestCase

from report.render import render_html


class RenderHtmlTests(TestCase):
    def _state(self):
        return {
            "report_date": "2026-08-20",
            "metrics": {
                "reporting_farms": 75,
                "total_harvest_yield_kg": 1640000,
                "total_energy_kwh": 6215600,
                "energy_efficiency_kwh_per_kg": 3.79,
                "waste_reduction_progress": 0.0666,
                "environmental_compliance_rate": 0.973,
                "sensor_anomaly_rate": 0.012,
                "total_sensor_readings": 18040,
            },
            "narrative": (
                "UrbanGreen reported stable daily operational "
                "performance across 75 reporting farms."
            ),
            "insights": [
                "UG Farm 25 ranked first on the daily leaderboard.",
                "Temperature readings recorded a 0.1% anomaly rate.",
            ],
            "top_farms": [
                {
                    "rank": 1,
                    "farm": "UG Farm 25",
                    "city": "Cologne",
                    "total_yield_kg": 20300,
                    "premium_yield_share": 0.3972,
                    "energy_efficiency_kwh_per_kg": 3.79,
                }
            ],
            "sensors": [
                {
                    "sensor_type": "Temperature",
                    "unit": "°C",
                    "readings": 3010,
                    "anomalies": 2,
                    "anomaly_rate": 0.00066,
                    "compliance_rate": 0.982,
                }
            ],
        }

    def test_render_html_contains_report_content(self):
        result = render_html(self._state())

        html = result["html"]

        # Header
        self.assertIn("UrbanGreen Analytics", html)
        self.assertIn("Daily Executive Report", html)
        self.assertIn("2026-08-20", html)

        # Main sections
        self.assertIn("Key Figures", html)
        self.assertIn("Summary", html)
        self.assertIn("Key Insights", html)
        self.assertIn("Top Farms", html)
        self.assertIn("Sensor Overview", html)

        # Eight KPI cards
        self.assertEqual(html.count('class="kpi-card"'), 8)

        # Key figures
        self.assertIn("Total Harvest Yield", html)
        self.assertIn("1,640,000.0", html)

        self.assertIn("Total Energy Consumption", html)
        self.assertIn("6,215,600.0", html)

        self.assertIn("Energy Efficiency", html)
        self.assertIn("3.79", html)

        self.assertIn("Waste Reduction Progress", html)
        self.assertIn("6.7%", html)

        self.assertIn("Environmental Compliance", html)
        self.assertIn("97.3%", html)

        self.assertIn("Sensor Anomaly Rate", html)
        self.assertIn("1.2%", html)

        self.assertIn("Reporting Farms", html)
        self.assertIn(">75<", html.replace("\n", "").replace(" ", ""))

        self.assertIn("Total Sensor Readings", html)
        self.assertIn("18,040", html)

        # Top farms
        self.assertIn("UG Farm 25", html)
        self.assertIn("Cologne", html)
        self.assertIn("20,300.0", html)
        self.assertIn("39.7%", html)

        # Sensor overview
        self.assertIn("Temperature", html)
        self.assertIn("3,010", html)
        self.assertIn("98.2%", html)

        # LLM-generated content
        self.assertIn("stable daily operational performance", html)
        self.assertIn("ranked first on the daily leaderboard", html)

    def test_render_html_escapes_dynamic_content(self):
        state = self._state()

        state["narrative"] = "<script>alert('summary')</script>"
        state["insights"] = ["<b>unsafe insight</b>", "Safe insight"]
        state["top_farms"][0]["farm"] = "<script>alert('farm')</script>"
        state["sensors"][0]["sensor_type"] = "<img src=x onerror=alert('sensor')>"

        result = render_html(state)

        html = result["html"]

        self.assertNotIn("<script>alert('summary')</script>", html)
        self.assertNotIn("<b>unsafe insight</b>", html)
        self.assertNotIn("<script>alert('farm')</script>", html)
        self.assertNotIn("<img src=x onerror=alert('sensor')>", html)

        self.assertIn("&lt;script&gt;", html)
        self.assertIn("&lt;b&gt;unsafe insight&lt;/b&gt;", html)
        self.assertIn("&lt;img", html)

    def test_render_html_has_no_external_assets(self):
        result = render_html(self._state())

        html = result["html"].lower()

        self.assertNotIn("<script", html)
        self.assertNotIn("<link", html)
        self.assertNotIn("@import", html)
        self.assertNotIn("http://", html)
        self.assertNotIn("https://", html)
