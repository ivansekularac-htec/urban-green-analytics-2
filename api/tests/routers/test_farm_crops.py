"""Tests for /farm-crops/ endpoints."""

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
    category = client.post("/api/v1/crop-categories/", json={"name": "Herbs"}).json()
    crop = client.post(
        "/api/v1/crops/", json={"name": "Basil", "category_id": category["id"]}
    ).json()
    return {"farm_id": farm["id"], "crop_id": crop["id"]}


def farm_crop_payload(prereqs, **overrides):
    base = {
        "farm_id": prereqs["farm_id"],
        "crop_id": prereqs["crop_id"],
        "started_at": 1700000000,
    }
    return {**base, **overrides}


def test_list_empty(client):
    r = client.get("/api/v1/farm-crops/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client, prereqs):
    r = client.post("/api/v1/farm-crops/", json=farm_crop_payload(prereqs))
    assert r.status_code == 201
    data = r.json()
    assert data["farm_id"] == prereqs["farm_id"]
    assert data["crop_id"] == prereqs["crop_id"]


def test_create_missing_started_at(client, prereqs):
    r = client.post(
        "/api/v1/farm-crops/",
        json={"farm_id": prereqs["farm_id"], "crop_id": prereqs["crop_id"]},
    )
    assert r.status_code == 422


def test_get(client, prereqs):
    created = client.post("/api/v1/farm-crops/", json=farm_crop_payload(prereqs)).json()
    r = client.get(f"/api/v1/farm-crops/{created['id']}")
    assert r.status_code == 200


def test_get_not_found(client):
    r = client.get("/api/v1/farm-crops/999")
    assert r.status_code == 404


def test_update(client, prereqs):
    created = client.post("/api/v1/farm-crops/", json=farm_crop_payload(prereqs)).json()
    r = client.put(f"/api/v1/farm-crops/{created['id']}", json={"ended_at": 1800000000})
    assert r.status_code == 200
    assert r.json()["ended_at"] == 1800000000


def test_update_not_found(client):
    r = client.put("/api/v1/farm-crops/999", json={"ended_at": 1800000000})
    assert r.status_code == 404


def test_delete(client, prereqs):
    created = client.post("/api/v1/farm-crops/", json=farm_crop_payload(prereqs)).json()
    r = client.delete(f"/api/v1/farm-crops/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/farm-crops/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/farm-crops/999")
    assert r.status_code == 404
