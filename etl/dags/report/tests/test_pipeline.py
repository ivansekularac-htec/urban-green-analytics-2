"""Tests for the executive report LangGraph pipeline."""

from unittest import TestCase
from unittest.mock import MagicMock, patch

import report.pipeline as pipeline


class ReportPipelineTests(TestCase):
    def test_graph_runs_stages_in_linear_order(self):
        calls = []

        def retrieve(state):
            calls.append("retrieve_metrics")

            self.assertEqual(state["report_date"], "2026-08-20")

            return {"metrics": {"reporting_farms": 75}}

        def summarize(state):
            calls.append("summarize_metrics")

            self.assertIn("metrics", state)

            return {
                "narrative": "Summary.",
                "insights": ["Insight one.", "Insight two."],
            }

        def render(state):
            calls.append("render_html")

            self.assertEqual(state["narrative"], "Summary.")

            return {"html": "<html>report</html>"}

        def publish(state):
            calls.append("publish_report")

            self.assertEqual(state["html"], "<html>report</html>")

            return {"object_key": ("reports/executive/date=2026-08-20/report.html")}

        with (
            patch.object(pipeline, "retrieve_metrics", new=retrieve),
            patch.object(pipeline, "summarize_metrics", new=summarize),
            patch.object(pipeline, "render_html", new=render),
            patch.object(pipeline, "publish_report", new=publish),
        ):
            graph = pipeline._build_graph()

            result = graph.invoke({"report_date": "2026-08-20"})

        self.assertEqual(
            calls,
            [
                "retrieve_metrics",
                "summarize_metrics",
                "render_html",
                "publish_report",
            ],
        )

        self.assertEqual(
            result["object_key"], ("reports/executive/date=2026-08-20/report.html")
        )

    def test_run_report_passes_report_date_to_graph(self):
        graph = MagicMock()

        graph.invoke.return_value = {
            "object_key": ("reports/executive/date=2026-08-20/report.html")
        }

        with patch.object(pipeline, "REPORT_GRAPH", graph):
            result = pipeline.run_report("2026-08-20")

        graph.invoke.assert_called_once_with({"report_date": "2026-08-20"})

        self.assertEqual(result, ("reports/executive/date=2026-08-20/report.html"))

    def test_run_report_rejects_invalid_date(self):
        graph = MagicMock()

        with patch.object(pipeline, "REPORT_GRAPH", graph):
            with self.assertRaises(ValueError):
                pipeline.run_report("invalid-date")

        graph.invoke.assert_not_called()

    def test_main_runs_report_for_cli_date(self):
        expected_key = "reports/executive/date=2026-08-20/report.html"

        with (
            patch("sys.argv", ["report.pipeline", "--date", "2026-08-20"]),
            patch.object(
                pipeline,
                "run_report",
                return_value=expected_key,
            ) as run_report,
            patch("builtins.print") as print_mock,
        ):
            pipeline.main()

        run_report.assert_called_once_with("2026-08-20")

        print_mock.assert_called_once_with(expected_key)
