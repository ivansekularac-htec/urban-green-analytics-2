"""
test_crops.py
Tests for crop CRUD endpoints.
"""


def create_crop_category(client) -> int:
    response = client.post(
        "/api/v1/crop-categories",
        json={
            "name": "Herbs",
            "description": "Herb crops",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_crop_payload(category_id: int) -> dict[str, object]:
    return {
        "category_id": category_id,
        "name": "Basil",
        "description": "Fresh basil crop",
    }


def test_create_crop(client):
    category_id = create_crop_category(client)

    response = client.post(
        "/api/v1/crops",
        json=create_crop_payload(category_id),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["category_id"] == category_id
    assert data["name"] == "Basil"
    assert data["description"] == "Fresh basil crop"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_crop_invalid_input(client):
    response = client.post(
        "/api/v1/crops",
        json={
            "description": "Missing category_id and name",
        },
    )

    assert response.status_code == 422


def test_create_crop_with_missing_category(client):
    response = client.post(
        "/api/v1/crops",
        json=create_crop_payload(999),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found."


def test_get_crops(client):
    category_id = create_crop_category(client)

    client.post(
        "/api/v1/crops",
        json=create_crop_payload(category_id),
    )

    response = client.get("/api/v1/crops")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["category_id"] == category_id
    assert data[0]["name"] == "Basil"


def test_get_crop(client):
    category_id = create_crop_category(client)

    create_response = client.post(
        "/api/v1/crops",
        json=create_crop_payload(category_id),
    )

    crop_id = create_response.json()["id"]

    response = client.get(f"/api/v1/crops/{crop_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == crop_id
    assert data["category_id"] == category_id
    assert data["name"] == "Basil"


def test_get_crop_not_found(client):
    response = client.get("/api/v1/crops/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found."


def test_update_crop(client):
    category_id = create_crop_category(client)

    create_response = client.post(
        "/api/v1/crops",
        json=create_crop_payload(category_id),
    )

    crop_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/crops/{crop_id}",
        json={
            "category_id": category_id,
            "name": "Updated Basil",
            "description": "Updated crop description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == crop_id
    assert data["category_id"] == category_id
    assert data["name"] == "Updated Basil"
    assert data["description"] == "Updated crop description"


def test_update_crop_partial(client):
    category_id = create_crop_category(client)

    create_response = client.post(
        "/api/v1/crops",
        json=create_crop_payload(category_id),
    )

    crop_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/crops/{crop_id}",
        json={
            "description": "Partially updated crop description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["category_id"] == category_id
    assert data["name"] == "Basil"
    assert data["description"] == "Partially updated crop description"


def test_update_crop_not_found(client):
    response = client.put(
        "/api/v1/crops/999",
        json={
            "name": "Missing Crop",
            "description": "Missing crop description",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found."


def test_update_crop_with_missing_category(client):
    category_id = create_crop_category(client)

    create_response = client.post(
        "/api/v1/crops",
        json=create_crop_payload(category_id),
    )

    crop_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/crops/{crop_id}",
        json={
            "category_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found."


def test_delete_crop(client):
    category_id = create_crop_category(client)

    create_response = client.post(
        "/api/v1/crops",
        json=create_crop_payload(category_id),
    )

    crop_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/crops/{crop_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/crops/{crop_id}")

    assert get_response.status_code == 404


def test_delete_crop_not_found(client):
    response = client.delete("/api/v1/crops/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found."
