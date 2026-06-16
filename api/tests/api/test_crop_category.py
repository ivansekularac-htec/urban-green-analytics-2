"""
test_crop_categories.py
Tests for crop category CRUD endpoints.
"""


def test_create_crop_category(client):
    response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Leafy Greens",
            "description": "Leaf-based crops",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Leafy Greens"
    assert data["description"] == "Leaf-based crops"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_crop_category_invalid_input(client):
    response = client.post(
        "/api/v1/crop-categories",
        json={
            "description": "Missing required name",
        },
    )

    assert response.status_code == 422


def test_get_crop_categories(client):
    client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Herbs",
            "description": "Herb crops",
        },
    )

    response = client.get("/api/v1/crop-categories")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Herbs"
    assert data[0]["description"] == "Herb crops"


def test_get_crop_category(client):
    create_response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Microgreens",
            "description": "Microgreen crops",
        },
    )

    crop_category_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/crop-categories/{crop_category_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == crop_category_id
    assert data["name"] == "Microgreens"
    assert data["description"] == "Microgreen crops"


def test_get_crop_category_not_found(client):
    response = client.get("/api/v1/crop-categories/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found."


def test_update_crop_category(client):
    create_response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Old Category",
            "description": "Old description",
        },
    )

    crop_category_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/crop-categories/{crop_category_id}",
        json={
            "name": "Updated Category",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == crop_category_id
    assert data["name"] == "Updated Category"
    assert data["description"] == "Updated description"


def test_update_crop_category_partial(client):
    create_response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Partial Category",
            "description": "Original description",
        },
    )

    crop_category_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/crop-categories/{crop_category_id}",
        json={
            "description": "Partially updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Partial Category"
    assert data["description"] == "Partially updated description"


def test_update_crop_category_not_found(client):
    response = client.put(
        "/api/v1/crop-categories/999",
        json={
            "name": "Missing Category",
            "description": "Missing description",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found."


def test_delete_crop_category(client):
    create_response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Delete Category",
            "description": "To be deleted",
        },
    )

    crop_category_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/crop-categories/{crop_category_id}",
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/crop-categories/{crop_category_id}",
    )

    assert get_response.status_code == 404


def test_delete_crop_category_not_found(client):
    response = client.delete("/api/v1/crop-categories/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found."
