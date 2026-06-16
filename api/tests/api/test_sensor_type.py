"""
test_sensor_types.py
Tests for sensor type CRUD endpoints.
"""

from decimal import Decimal


def test_create_sensor_type(client):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
            "unit": "°C",
            "description": "Measures air temperature",
            "optimal_min": "18.000",
            "optimal_max": "26.000",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Temperature"
    assert data["unit"] == "°C"
    assert data["description"] == "Measures air temperature"
    assert Decimal(data["optimal_min"]) == Decimal("18.000")
    assert Decimal(data["optimal_max"]) == Decimal("26.000")
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_sensor_type_invalid_input(client):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "description": "Missing required name and unit",
        },
    )

    assert response.status_code == 422


def test_get_sensor_types(client):
    client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Humidity",
            "unit": "%",
            "description": "Measures relative humidity",
            "optimal_min": "40.000",
            "optimal_max": "70.000",
        },
    )

    response = client.get("/api/v1/sensor-types")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["name"] == "Humidity"
    assert data[0]["unit"] == "%"
    assert data[0]["description"] == "Measures relative humidity"


def test_get_sensor_type(client):
    create_response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "CO2",
            "unit": "ppm",
            "description": "Measures carbon dioxide concentration",
            "optimal_min": "400.000",
            "optimal_max": "1200.000",
        },
    )

    sensor_type_id = create_response.json()["id"]

    response = client.get(f"/api/v1/sensor-types/{sensor_type_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == sensor_type_id
    assert data["name"] == "CO2"
    assert data["unit"] == "ppm"


def test_get_sensor_type_not_found(client):
    response = client.get("/api/v1/sensor-types/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found."


def test_update_sensor_type(client):
    create_response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Light",
            "unit": "lux",
            "description": "Old description",
            "optimal_min": "100.000",
            "optimal_max": "500.000",
        },
    )

    sensor_type_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sensor-types/{sensor_type_id}",
        json={
            "name": "Light Intensity",
            "unit": "lux",
            "description": "Updated description",
            "optimal_min": "150.000",
            "optimal_max": "600.000",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == sensor_type_id
    assert data["name"] == "Light Intensity"
    assert data["unit"] == "lux"
    assert data["description"] == "Updated description"
    assert Decimal(data["optimal_min"]) == Decimal("150.000")
    assert Decimal(data["optimal_max"]) == Decimal("600.000")


def test_update_sensor_type_partial(client):
    create_response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "pH",
            "unit": "pH",
            "description": "Measures acidity",
            "optimal_min": "5.500",
            "optimal_max": "6.500",
        },
    )

    sensor_type_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sensor-types/{sensor_type_id}",
        json={
            "description": "Partially updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "pH"
    assert data["unit"] == "pH"
    assert data["description"] == "Partially updated description"


def test_update_sensor_type_not_found(client):
    response = client.put(
        "/api/v1/sensor-types/999",
        json={
            "name": "Missing Sensor Type",
            "unit": "unit",
            "description": "Missing description",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found."


def test_delete_sensor_type(client):
    create_response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Energy",
            "unit": "kWh",
            "description": "Measures energy consumption",
            "optimal_min": "0.000",
            "optimal_max": "100.000",
        },
    )

    sensor_type_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/sensor-types/{sensor_type_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/sensor-types/{sensor_type_id}")

    assert get_response.status_code == 404


def test_delete_sensor_type_not_found(client):
    response = client.delete("/api/v1/sensor-types/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found."
