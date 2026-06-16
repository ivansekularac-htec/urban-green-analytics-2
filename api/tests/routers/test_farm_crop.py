def test_create_farm_crop(client):
    response = client.post(
        "/api/v1/farm_crop/",
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


def test_get_farm_crop(client):
    response = client.get("/api/v1/farm_crop/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_delete_farm_crop(client):
    response = client.delete(
        "/api/v1/farm_crop/999999",
    )

    assert response.status_code == 404
