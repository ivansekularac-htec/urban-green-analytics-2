"""Tests for /sensor-types/ endpoints."""


def test_list_empty(client):
    r = client.get("/api/v1/sensor-types/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client):
    r = client.post("/api/v1/sensor-types/", json={"name": "Temperature", "unit": "°C"})
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Temperature"
    assert data["unit"] == "°C"


def test_create_missing_name(client):
    r = client.post("/api/v1/sensor-types/", json={"unit": "°C"})
    assert r.status_code == 422


def test_create_missing_unit(client):
    r = client.post("/api/v1/sensor-types/", json={"name": "Humidity"})
    assert r.status_code == 422


def test_get(client):
    created = client.post("/api/v1/sensor-types/", json={"name": "CO2", "unit": "ppm"}).json()
    r = client.get(f"/api/v1/sensor-types/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "CO2"


def test_get_not_found(client):
    r = client.get("/api/v1/sensor-types/999")
    assert r.status_code == 404


def test_update(client):
    created = client.post("/api/v1/sensor-types/", json={"name": "Old", "unit": "x"}).json()
    r = client.put(f"/api/v1/sensor-types/{created['id']}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"


def test_update_not_found(client):
    r = client.put("/api/v1/sensor-types/999", json={"name": "X"})
    assert r.status_code == 404


def test_delete(client):
    created = client.post("/api/v1/sensor-types/", json={"name": "Light", "unit": "lux"}).json()
    r = client.delete(f"/api/v1/sensor-types/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/sensor-types/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/sensor-types/999")
    assert r.status_code == 404
