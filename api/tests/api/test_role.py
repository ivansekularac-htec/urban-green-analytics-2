"""
test_roles.py
Tests for role CRUD endpoints.
"""


def test_create_role(client):
    response = client.post(
        "/api/v1/roles",
        json={
            "name": "Test Role",
            "description": "Test description",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Role"
    assert data["description"] == "Test description"
    assert "id" in data


def test_get_roles(client):
    client.post(
        "/api/v1/roles",
        json={
            "name": "Test Role",
            "description": "Test description",
        },
    )

    response = client.get("/api/v1/roles")

    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_role_not_found(client):
    response = client.get("/api/v1/roles/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found."


def test_update_role(client):
    create_response = client.post(
        "/api/v1/roles",
        json={
            "name": "Old Role",
            "description": "Old description",
        },
    )

    role_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/roles/{role_id}",
        json={
            "name": "Updated Role",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Role"
    assert data["description"] == "Updated description"


def test_update_role_not_found(client):
    response = client.put(
        "/api/v1/roles/999",
        json={
            "name": "Updated Role",
            "description": "Updated description",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found."


def test_delete_role(client):
    create_response = client.post(
        "/api/v1/roles",
        json={
            "name": "Role To Delete",
            "description": "Test description",
        },
    )

    role_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/roles/{role_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/roles/{role_id}")

    assert get_response.status_code == 404


def test_delete_role_not_found(client):
    response = client.delete("/api/v1/roles/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found."


def test_create_role_invalid_input(client):
    response = client.post(
        "/api/v1/roles",
        json={
            "description": "Missing required name",
        },
    )

    assert response.status_code == 422
