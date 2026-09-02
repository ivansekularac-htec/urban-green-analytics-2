"""Tests for the Prometheus `/metrics` endpoint.

These assert the contract the instrumentation must keep: that `/metrics` serves
Prometheus exposition without authentication, that a driven request is counted
under its matched route template rather than `unmatched`, and that the endpoint
stays out of the public OpenAPI schema. The startup hooks are patched so the
`TestClient` never talks to a real database, per the testing rules.
"""

from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


def _client() -> TestClient:
    with (
        patch("app.main.verify_database_connection"),
        patch("app.main.SessionLocal"),
        patch("app.main.ensure_superuser"),
        patch("app.main.ensure_demo_users"),
    ):
        return TestClient(app)


def test_metrics_endpoint_exposes_prometheus_metrics():
    client = _client()

    # Drive one request so the request counter has a sample to expose.
    assert client.get("/health").status_code == 200

    response = client.get("/metrics")

    assert response.status_code == 200
    # Prometheus exposition format, served without a token.
    assert response.headers["content-type"].startswith("text/plain")
    assert "version=" in response.headers["content-type"]

    body = response.text
    assert "http_requests_total" in body
    assert "http_request_duration_seconds" in body
    # A runtime metric from the default instrumentation. `python_info` is
    # cross-platform; the `process_*` gauges are Linux-only (they read /proc),
    # so they are asserted in the manual Docker check rather than here.
    assert "python_info" in body


def test_request_is_counted_under_its_route_template_not_unmatched():
    """The instrumentation must sit before the routers, so a request is
    labelled with the route it matched rather than `unmatched`."""
    client = _client()

    client.get("/health")
    body = client.get("/metrics").text

    assert 'handler="/health"' in body
    assert 'handler="unmatched"' not in body


def test_metrics_is_hidden_from_the_openapi_schema():
    client = _client()

    paths = client.get("/openapi.json").json()["paths"]

    assert "/metrics" not in paths
