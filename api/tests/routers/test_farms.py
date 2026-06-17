"""Tests for /farms/ endpoints."""

import pytest


@pytest.fixture
def prereqs(client):
    """Create infrastructure and growing system types needed by Farm."""
    infra = client.post("/api/v1/infrastructure-types/", json={"name": "Hydroponic"}).json()
    growing = client.post("/api/v1/growing-system-types/", json={"name": "NFT"}).json()
    return {"infrastructure_type_id": infra["id"], "growing_system_type_id": growing["id"]}


def farm_payload(prereqs, **overrides):
    base = {
        "name": "Test Farm",
        "infrastructure_type_id": prereqs["infrastructure_type_id"],
        "growing_system_type_id": prereqs["growing_system_type_id"],
    }
    return {**base, **overrides}


def test_list_empty(client):
    r = client.get("/api/v1/farms/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client, prereqs):
    r = client.post("/api/v1/farms/", json=farm_payload(prereqs))
    assert r.status_code == 201
    data = r.json()
    assert data["name"] == "Test Farm"
    assert "id" in data


def test_create_missing_name(client, prereqs):
    payload = {
        "infrastructure_type_id": prereqs["infrastructure_type_id"],
        "growing_system_type_id": prereqs["growing_system_type_id"],
    }
    r = client.post("/api/v1/farms/", json=payload)
    assert r.status_code == 422


def test_get(client, prereqs):
    created = client.post("/api/v1/farms/", json=farm_payload(prereqs, name="Farm A")).json()
    r = client.get(f"/api/v1/farms/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Farm A"


def test_get_not_found(client):
    r = client.get("/api/v1/farms/999")
    assert r.status_code == 404


def test_update(client, prereqs):
    created = client.post("/api/v1/farms/", json=farm_payload(prereqs)).json()
    r = client.put(f"/api/v1/farms/{created['id']}", json={"name": "Updated Farm"})
    assert r.status_code == 200
    assert r.json()["name"] == "Updated Farm"


def test_update_not_found(client):
    r = client.put("/api/v1/farms/999", json={"name": "X"})
    assert r.status_code == 404


def test_delete(client, prereqs):
    created = client.post("/api/v1/farms/", json=farm_payload(prereqs)).json()
    r = client.delete(f"/api/v1/farms/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/farms/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/farms/999")
    assert r.status_code == 404


def test_list_multiple(client, prereqs):
    client.post("/api/v1/farms/", json=farm_payload(prereqs, name="Farm 1"))
    client.post("/api/v1/farms/", json=farm_payload(prereqs, name="Farm 2"))
    r = client.get("/api/v1/farms/")
    assert len(r.json()) == 2
