"""Tests for /roles/ endpoints."""


def test_list_empty(client):
    r = client.get("/api/v1/roles/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client):
    r = client.post("/api/v1/roles/", json={"name": "Admin"})
    assert r.status_code == 201
    assert r.json()["name"] == "Admin"


def test_create_missing_name(client):
    r = client.post("/api/v1/roles/", json={})
    assert r.status_code == 422


def test_get(client):
    created = client.post("/api/v1/roles/", json={"name": "Viewer"}).json()
    r = client.get(f"/api/v1/roles/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Viewer"


def test_get_not_found(client):
    r = client.get("/api/v1/roles/999")
    assert r.status_code == 404


def test_update(client):
    created = client.post("/api/v1/roles/", json={"name": "Old"}).json()
    r = client.put(f"/api/v1/roles/{created['id']}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"


def test_update_not_found(client):
    r = client.put("/api/v1/roles/999", json={"name": "X"})
    assert r.status_code == 404


def test_delete(client):
    created = client.post("/api/v1/roles/", json={"name": "To Delete"}).json()
    r = client.delete(f"/api/v1/roles/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/roles/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/roles/999")
    assert r.status_code == 404
