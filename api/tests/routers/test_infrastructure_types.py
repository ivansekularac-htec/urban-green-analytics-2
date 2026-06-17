"""Tests for /infrastructure-types/ endpoints."""


def test_list_empty(client):
    r = client.get("/api/v1/infrastructure-types/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client):
    r = client.post("/api/v1/infrastructure-types/", json={"name": "Hydroponic"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Hydroponic"
    assert "id" in data


def test_create_missing_name(client):
    r = client.post("/api/v1/infrastructure-types/", json={"description": "No name"})
    assert r.status_code == 422


def test_get(client):
    created = client.post("/api/v1/infrastructure-types/", json={"name": "Aeroponic"}).json()
    r = client.get(f"/api/v1/infrastructure-types/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Aeroponic"


def test_get_not_found(client):
    r = client.get("/api/v1/infrastructure-types/999")
    assert r.status_code == 404


def test_update(client):
    created = client.post("/api/v1/infrastructure-types/", json={"name": "Old Name"}).json()
    r = client.put(f"/api/v1/infrastructure-types/{created['id']}", json={"name": "New Name"})
    assert r.status_code == 200
    assert r.json()["name"] == "New Name"


def test_update_not_found(client):
    r = client.put("/api/v1/infrastructure-types/999", json={"name": "X"})
    assert r.status_code == 404


def test_delete(client):
    created = client.post("/api/v1/infrastructure-types/", json={"name": "To Delete"}).json()
    r = client.delete(f"/api/v1/infrastructure-types/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/infrastructure-types/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/infrastructure-types/999")
    assert r.status_code == 404


def test_list_multiple(client):
    client.post("/api/v1/infrastructure-types/", json={"name": "A"})
    client.post("/api/v1/infrastructure-types/", json={"name": "B"})
    r = client.get("/api/v1/infrastructure-types/")
    assert len(r.json()) == 2
