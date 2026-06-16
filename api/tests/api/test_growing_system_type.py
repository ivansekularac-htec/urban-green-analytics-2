"""
test_growing_system_types.py
Tests for growing system type CRUD endpoints.
"""


def test_create_growing_system_type(client):
    response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Tower",
            "description": "Vertical tower growing system",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Tower"
    assert data["description"] == "Vertical tower growing system"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_growing_system_type_invalid_input(client):
    response = client.post(
        "/api/v1/growing-system-types",
        json={
            "description": "Missing required name",
        },
    )

    assert response.status_code == 422


def test_get_growing_system_types(client):
    client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Flat Bed",
            "description": "Flat growing bed system",
        },
    )

    response = client.get("/api/v1/growing-system-types")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Flat Bed"
    assert data[0]["description"] == "Flat growing bed system"


def test_get_growing_system_type(client):
    create_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Vertical",
            "description": "Vertical growing system",
        },
    )

    growing_system_type_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/growing-system-types/{growing_system_type_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == growing_system_type_id
    assert data["name"] == "Vertical"
    assert data["description"] == "Vertical growing system"


def test_get_growing_system_type_not_found(client):
    response = client.get("/api/v1/growing-system-types/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Growing system type not found."


def test_update_growing_system_type(client):
    create_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Old Growing System",
            "description": "Old description",
        },
    )

    growing_system_type_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/growing-system-types/{growing_system_type_id}",
        json={
            "name": "Updated Growing System",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == growing_system_type_id
    assert data["name"] == "Updated Growing System"
    assert data["description"] == "Updated description"


def test_update_growing_system_type_partial(client):
    create_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Partial Growing System",
            "description": "Original description",
        },
    )

    growing_system_type_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/growing-system-types/{growing_system_type_id}",
        json={
            "description": "Partially updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Partial Growing System"
    assert data["description"] == "Partially updated description"


def test_update_growing_system_type_not_found(client):
    response = client.put(
        "/api/v1/growing-system-types/999",
        json={
            "name": "Missing Growing System",
            "description": "Missing description",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Growing system type not found."


def test_delete_growing_system_type(client):
    create_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Delete Growing System",
            "description": "To be deleted",
        },
    )

    growing_system_type_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/growing-system-types/{growing_system_type_id}",
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/growing-system-types/{growing_system_type_id}",
    )

    assert get_response.status_code == 404


def test_delete_growing_system_type_not_found(client):
    response = client.delete("/api/v1/growing-system-types/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Growing system type not found."
