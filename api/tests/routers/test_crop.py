def test_get_crops(client):
    response = client.get("/api/v1/crops/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_crop(client):
    response = client.post(
        "/api/v1/crops/",
        json={
            "name": "Lettuce",
            "description": "Green lettuce",
            "category_id": 1,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Lettuce"
    assert data["category_id"] == 1


def test_create_crop_invalid_payload(client):
    response = client.post(
        "/api/v1/crops/",
        json={},
    )

    assert response.status_code == 422


def test_update_crop_not_found(client):
    response = client.put(
        "/api/v1/crops/999999",
        json={
            "name": "Updated Crop",
        },
    )

    assert response.status_code == 404


def test_delete_crop_not_found(client):
    response = client.delete(
        "/api/v1/crops/999999",
    )

    assert response.status_code == 404
