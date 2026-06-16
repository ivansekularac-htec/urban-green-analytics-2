def test_get_crop_categories(client):
    response = client.get("/api/v1/crop-categories/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_crop_category(client):
    response = client.post(
        "/api/v1/crop-categories/",
        json={
            "name": "Leafy Greens",
            "description": "Crops grown primarily for their edible leaves",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Leafy Greens"


def test_create_crop_category_invalid_payload(client):
    response = client.post(
        "/api/v1/crop-categories/",
        json={},
    )

    assert response.status_code == 422


def test_update_crop_category_not_found(client):
    response = client.put(
        "/api/v1/crop-categories/999999",
        json={
            "name": "Updated Category",
        },
    )

    assert response.status_code == 404
