def test_create_sensor_type(client):
    response = client.post(
        "/api/v1/sensor_type/",
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


def test_get_sensor_type(client):
    response = client.get("/api/v1/sensor_type/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
