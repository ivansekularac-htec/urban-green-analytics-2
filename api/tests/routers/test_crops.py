"""Tests for /crops/ endpoints."""

import pytest


@pytest.fixture
def category(client):
    return client.post("/api/v1/crop-categories/", json={"name": "Leafy Greens"}).json()


def test_list_empty(client):
    r = client.get("/api/v1/crops/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client, category):
    r = client.post("/api/v1/crops/", json={"name": "Lettuce", "category_id": category["id"]})
    assert r.status_code == 201
    assert r.json()["name"] == "Lettuce"


def test_create_missing_name(client, category):
    r = client.post("/api/v1/crops/", json={"category_id": category["id"]})
    assert r.status_code == 422


def test_get(client, category):
    created = client.post(
        "/api/v1/crops/", json={"name": "Basil", "category_id": category["id"]}
    ).json()
    r = client.get(f"/api/v1/crops/{created['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Basil"


def test_get_not_found(client):
    r = client.get("/api/v1/crops/999")
    assert r.status_code == 404


def test_update(client, category):
    created = client.post(
        "/api/v1/crops/", json={"name": "Old", "category_id": category["id"]}
    ).json()
    r = client.put(f"/api/v1/crops/{created['id']}", json={"name": "New"})
    assert r.status_code == 200
    assert r.json()["name"] == "New"


def test_update_not_found(client):
    r = client.put("/api/v1/crops/999", json={"name": "X"})
    assert r.status_code == 404


def test_delete(client, category):
    created = client.post(
        "/api/v1/crops/", json={"name": "Mint", "category_id": category["id"]}
    ).json()
    r = client.delete(f"/api/v1/crops/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/crops/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/crops/999")
    assert r.status_code == 404
