"""Tests for the Prometheus metrics endpoint."""


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    """Expose HTTP and runtime metrics without authentication or a live database."""
    health_response = client.get("/health")
    assert health_response.status_code == 200

    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "http_requests_total" in response.text
    assert "http_request_duration_seconds" in response.text
    assert 'handler="/health"' in response.text
    assert "python_info" in response.text

    openapi_response = client.get("/openapi.json")
    assert openapi_response.status_code == 200
    assert "/metrics" not in openapi_response.json()["paths"]
