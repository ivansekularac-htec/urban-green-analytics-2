"""Tests for /user-roles/ endpoints."""

import pytest


@pytest.fixture
def prereqs(client):
    user = client.post(
        "/api/v1/users/",
        json={"email": "u@example.com", "full_name": "User", "password": "password123"},
    ).json()
    role = client.post("/api/v1/roles/", json={"name": "Admin"}).json()
    return {"user_id": user["id"], "role_id": role["id"]}


def test_list_empty(client):
    r = client.get("/api/v1/user-roles/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client, prereqs):
    r = client.post(
        "/api/v1/user-roles/",
        json={"user_id": prereqs["user_id"], "role_id": prereqs["role_id"]},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["user_id"] == prereqs["user_id"]
    assert data["role_id"] == prereqs["role_id"]


def test_create_missing_user_id(client, prereqs):
    r = client.post("/api/v1/user-roles/", json={"role_id": prereqs["role_id"]})
    assert r.status_code == 422


def test_get(client, prereqs):
    created = client.post(
        "/api/v1/user-roles/",
        json={"user_id": prereqs["user_id"], "role_id": prereqs["role_id"]},
    ).json()
    r = client.get(f"/api/v1/user-roles/{created['id']}")
    assert r.status_code == 200


def test_get_not_found(client):
    r = client.get("/api/v1/user-roles/999")
    assert r.status_code == 404


def test_update(client, prereqs):
    created = client.post(
        "/api/v1/user-roles/",
        json={"user_id": prereqs["user_id"], "role_id": prereqs["role_id"]},
    ).json()
    role2 = client.post("/api/v1/roles/", json={"name": "Viewer"}).json()
    r = client.put(f"/api/v1/user-roles/{created['id']}", json={"role_id": role2["id"]})
    assert r.status_code == 200
    assert r.json()["role_id"] == role2["id"]


def test_update_not_found(client):
    r = client.put("/api/v1/user-roles/999", json={"role_id": 1})
    assert r.status_code == 404


def test_delete(client, prereqs):
    created = client.post(
        "/api/v1/user-roles/",
        json={"user_id": prereqs["user_id"], "role_id": prereqs["role_id"]},
    ).json()
    r = client.delete(f"/api/v1/user-roles/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/user-roles/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/user-roles/999")
    assert r.status_code == 404
