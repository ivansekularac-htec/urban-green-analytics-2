import pytest


def test_get_harvests(client):
    response = client.get("/api/v1/harvests/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_harvest(client):
    response = client.post(
        "/api/v1/harvests/",
        json={
            "farm_id": 1,
            "crop_id": 1,
            "quality_grade_id": 1,
            "weight_kg": "25.50",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == 1
    assert data["crop_id"] == 1
    assert data["quality_grade_id"] == 1
    assert float(data["weight_kg"]) == pytest.approx(25.50)


def test_create_harvest_invalid_payload(client):
    response = client.post(
        "/api/v1/harvests/",
        json={},
    )

    assert response.status_code == 422


def test_update_harvest_not_found(client):
    response = client.put(
        "/api/v1/harvests/999999",
        json={
            "weight_kg": "30.00",
        },
    )

    assert response.status_code == 404
