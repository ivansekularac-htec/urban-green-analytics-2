"""Tests for /harvests/ endpoints."""

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
    grade = client.post("/api/v1/quality-grades/", json={"code": "A", "name": "Premium"}).json()
    return {"farm_id": farm["id"], "crop_id": crop["id"], "quality_grade_id": grade["id"]}


def harvest_payload(prereqs, **overrides):
    base = {
        "farm_id": prereqs["farm_id"],
        "crop_id": prereqs["crop_id"],
        "quality_grade_id": prereqs["quality_grade_id"],
        "weight_kg": "10.500",
    }
    return {**base, **overrides}


def test_list_empty(client):
    r = client.get("/api/v1/harvests/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client, prereqs):
    r = client.post("/api/v1/harvests/", json=harvest_payload(prereqs))
    assert r.status_code == 201
    assert float(r.json()["weight_kg"]) == pytest.approx(10.5)


def test_create_missing_weight(client, prereqs):
    payload = {
        "farm_id": prereqs["farm_id"],
        "crop_id": prereqs["crop_id"],
        "quality_grade_id": prereqs["quality_grade_id"],
    }
    r = client.post("/api/v1/harvests/", json=payload)
    assert r.status_code == 422


def test_get(client, prereqs):
    created = client.post("/api/v1/harvests/", json=harvest_payload(prereqs)).json()
    r = client.get(f"/api/v1/harvests/{created['id']}")
    assert r.status_code == 200


def test_get_not_found(client):
    r = client.get("/api/v1/harvests/999")
    assert r.status_code == 404


def test_update(client, prereqs):
    created = client.post("/api/v1/harvests/", json=harvest_payload(prereqs)).json()
    r = client.put(f"/api/v1/harvests/{created['id']}", json={"weight_kg": "20.000"})
    assert r.status_code == 200
    assert float(r.json()["weight_kg"]) == pytest.approx(20.0)


def test_update_not_found(client):
    r = client.put("/api/v1/harvests/999", json={"weight_kg": "5.000"})
    assert r.status_code == 404


def test_delete(client, prereqs):
    created = client.post("/api/v1/harvests/", json=harvest_payload(prereqs)).json()
    r = client.delete(f"/api/v1/harvests/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/harvests/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/harvests/999")
    assert r.status_code == 404
