"""Tests for /quality-grades/ endpoints."""


def test_list_empty(client):
    r = client.get("/api/v1/quality-grades/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client):
    r = client.post("/api/v1/quality-grades/", json={"code": "A", "name": "Premium"})
    assert r.status_code == 201
    data = r.json()
    assert data["code"] == "A"
    assert data["name"] == "Premium"


def test_create_missing_code(client):
    r = client.post("/api/v1/quality-grades/", json={"name": "Premium"})
    assert r.status_code == 422


def test_create_missing_name(client):
    r = client.post("/api/v1/quality-grades/", json={"code": "A"})
    assert r.status_code == 422


def test_get(client):
    created = client.post("/api/v1/quality-grades/", json={"code": "B", "name": "Standard"}).json()
    r = client.get(f"/api/v1/quality-grades/{created['id']}")
    assert r.status_code == 200
    assert r.json()["code"] == "B"


def test_get_not_found(client):
    r = client.get("/api/v1/quality-grades/999")
    assert r.status_code == 404


def test_update(client):
    created = client.post("/api/v1/quality-grades/", json={"code": "C", "name": "Low"}).json()
    r = client.put(f"/api/v1/quality-grades/{created['id']}", json={"name": "Updated"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated"


def test_update_not_found(client):
    r = client.put("/api/v1/quality-grades/999", json={"name": "X"})
    assert r.status_code == 404


def test_delete(client):
    created = client.post("/api/v1/quality-grades/", json={"code": "D", "name": "Reject"}).json()
    r = client.delete(f"/api/v1/quality-grades/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/quality-grades/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/quality-grades/999")
    assert r.status_code == 404
