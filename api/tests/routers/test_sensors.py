"""Tests for /sensors/ endpoints."""

import pytest


@pytest.fixture
def prereqs(client):
    infra = client.post("/api/v1/infrastructure-types/", json={"name": "Hydroponic"}).json()
    growing = client.post("/api/v1/growing-system-types/", json={"name": "NFT"}).json()
    farm = client.post(
        "/api/v1/farms/",
        json={
            "name": "Test Farm",
            "infrastructure_type_id": infra["id"],
            "growing_system_type_id": growing["id"],
        },
    ).json()
    sensor_type = client.post("/api/v1/sensor-types/", json={"name": "Temperature", "unit": "°C"}).json()
    return {"farm_id": farm["id"], "sensor_type_id": sensor_type["id"]}


def sensor_payload(prereqs, **overrides):
    base = {
        "farm_id": prereqs["farm_id"],
        "sensor_type_id": prereqs["sensor_type_id"],
        "serial_number": "SN-001",
    }
    return {**base, **overrides}


def test_list_empty(client):
    r = client.get("/api/v1/sensors/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client, prereqs):
    r = client.post("/api/v1/sensors/", json=sensor_payload(prereqs))
    assert r.status_code == 201
    assert r.json()["serial_number"] == "SN-001"


def test_create_missing_serial_number(client, prereqs):
    payload = {
        "farm_id": prereqs["farm_id"],
        "sensor_type_id": prereqs["sensor_type_id"],
    }
    r = client.post("/api/v1/sensors/", json=payload)
    assert r.status_code == 422


def test_get(client, prereqs):
    created = client.post("/api/v1/sensors/", json=sensor_payload(prereqs, serial_number="SN-ABC")).json()
    r = client.get(f"/api/v1/sensors/{created['id']}")
    assert r.status_code == 200
    assert r.json()["serial_number"] == "SN-ABC"


def test_get_not_found(client):
    r = client.get("/api/v1/sensors/999")
    assert r.status_code == 404


def test_update(client, prereqs):
    created = client.post("/api/v1/sensors/", json=sensor_payload(prereqs)).json()
    r = client.put(f"/api/v1/sensors/{created['id']}", json={"serial_number": "SN-UPDATED"})
    assert r.status_code == 200
    assert r.json()["serial_number"] == "SN-UPDATED"


def test_update_not_found(client):
    r = client.put("/api/v1/sensors/999", json={"serial_number": "X"})
    assert r.status_code == 404


def test_delete(client, prereqs):
    created = client.post("/api/v1/sensors/", json=sensor_payload(prereqs)).json()
    r = client.delete(f"/api/v1/sensors/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/sensors/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/sensors/999")
    assert r.status_code == 404
