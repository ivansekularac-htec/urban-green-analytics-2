def test_get_sensor_types(client):
    response = client.get("/api/v1/sensor-types/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_sensor_type(client):
    response = client.post(
        "/api/v1/sensor-types/",
        json={
            "name": "Temperature",
            "unit": "°C",
            "description": "Measures temperature",
            "optimal_min": "18.0",
            "optimal_max": "24.0",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Temperature"
    assert data["unit"] == "°C"


def test_create_sensor_type_invalid_payload(client):
    response = client.post(
        "/api/v1/sensor-types/",
        json={},
    )

    assert response.status_code == 422


def test_update_sensor_type_not_found(client):
    response = client.put(
        "/api/v1/sensor-types/999999",
        json={
            "name": "Updated Sensor Type",
        },
    )

    assert response.status_code == 404
