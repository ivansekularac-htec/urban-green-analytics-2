import pytest


def test_create_harvest(client):
    response = client.post(
        "/api/v1/harvest/",
        json={
            "farm_id": 1,
            "crop_id": 1,
            "quality_grade_id": 1,
            "weight_kg": 25.50,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == 1
    assert data["crop_id"] == 1
    assert data["quality_grade_id"] == 1
    assert float(data["weight_kg"]) == pytest.approx(25.50)


def test_get_harvest(client):
    response = client.get("/api/v1/harvest/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_harvest(client):
    create = client.post(
        "/api/v1/harvest/",
        json={"crop_id": 1, "farm_id": 1, "weight_kg": 25.50, "quality_grade_id": 1},
    )

    assert create.status_code == 201
    harvest_id = create.json()["id"]

    response = client.put(
        f"/api/v1/harvest/{harvest_id}",
        json={"weight_kg": 30.75},
    )

    assert response.status_code == 200
    data = response.json()

    assert float(data["weight_kg"]) == pytest.approx(30.75)


def test_delete_harvest(client):
    create = client.post(
        "/api/v1/harvest/",
        json={"crop_id": 1, "farm_id": 1, "weight_kg": 30.75, "quality_grade_id": 1},
    )
    harvest_id = create.json()["id"]

    response = client.delete(f"/api/v1/harvest/{harvest_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/harvest/{harvest_id}")
    assert get_response.status_code == 404
