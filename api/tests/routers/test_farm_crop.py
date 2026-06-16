def test_get_farm_crops(client):
    response = client.get("/api/v1/farm-crops/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_farm_crop(client):
    response = client.post(
        "/api/v1/farm-crops/",
        json={
            "farm_id": 1,
            "crop_id": 1,
            "started_at": 1750000000,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == 1
    assert data["crop_id"] == 1
    assert data["started_at"] == 1750000000


def test_create_farm_crop_invalid_payload(client):
    response = client.post(
        "/api/v1/farm-crops/",
        json={},
    )

    assert response.status_code == 422


def test_update_farm_crop_not_found(client):
    response = client.put(
        "/api/v1/farm-crops/999999",
        json={
            "started_at": 1750000000,
        },
    )

    assert response.status_code == 404
