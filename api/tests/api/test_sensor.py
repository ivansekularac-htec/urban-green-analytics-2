"""
test_sensors.py
Tests for sensor CRUD endpoints.
"""


def create_infrastructure_type(client) -> int:
    response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Hydroponic",
            "description": "Infrastructure",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_growing_system_type(client) -> int:
    response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Tower",
            "description": "Growing system",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_farm(client) -> int:
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_type_id,
            "growing_system_type_id": growing_system_type_id,
            "name": "Sensor Test Farm",
            "city": "Belgrade",
            "size_m2": "100.000",
            "status": "ACTIVE",
            "growing_beds_count": 10,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_sensor_type(client) -> int:
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
            "unit": "°C",
            "description": "Measures temperature",
            "optimal_min": "18.000",
            "optimal_max": "26.000",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_sensor_payload(
    farm_id: int,
    sensor_type_id: int,
) -> dict[str, object]:
    return {
        "farm_id": farm_id,
        "sensor_type_id": sensor_type_id,
        "serial_number": "SN-TEST-001",
        "status": "ACTIVE",
        "installed_at": 1710000000,
    }


def test_create_sensor(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == farm_id
    assert data["sensor_type_id"] == sensor_type_id
    assert data["serial_number"] == "SN-TEST-001"
    assert data["status"] == "ACTIVE"
    assert data["installed_at"] == 1710000000
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_sensor_invalid_input(client):
    response = client.post(
        "/api/v1/sensors",
        json={
            "serial_number": "SN-INVALID",
        },
    )

    assert response.status_code == 422


def test_create_sensor_with_missing_farm(client):
    sensor_type_id = create_sensor_type(client)

    response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            999,
            sensor_type_id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_create_sensor_with_missing_sensor_type(client):
    farm_id = create_farm(client)

    response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            999,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found."


def test_get_sensors(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    response = client.get("/api/v1/sensors")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["farm_id"] == farm_id
    assert data[0]["sensor_type_id"] == sensor_type_id
    assert data[0]["serial_number"] == "SN-TEST-001"


def test_get_sensor(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    create_response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    sensor_id = create_response.json()["id"]

    response = client.get(f"/api/v1/sensors/{sensor_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == sensor_id
    assert data["farm_id"] == farm_id
    assert data["sensor_type_id"] == sensor_type_id
    assert data["serial_number"] == "SN-TEST-001"


def test_get_sensor_not_found(client):
    response = client.get("/api/v1/sensors/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor not found."


def test_update_sensor(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    create_response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    sensor_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sensors/{sensor_id}",
        json={
            "farm_id": farm_id,
            "sensor_type_id": sensor_type_id,
            "serial_number": "SN-UPDATED-001",
            "status": "MAINTENANCE",
            "installed_at": 1720000000,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == sensor_id
    assert data["serial_number"] == "SN-UPDATED-001"
    assert data["status"] == "MAINTENANCE"
    assert data["installed_at"] == 1720000000


def test_update_sensor_partial(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    create_response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    sensor_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sensors/{sensor_id}",
        json={
            "status": "OFFLINE",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["serial_number"] == "SN-TEST-001"
    assert data["status"] == "OFFLINE"


def test_update_sensor_not_found(client):
    response = client.put(
        "/api/v1/sensors/999",
        json={
            "status": "OFFLINE",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor not found."


def test_update_sensor_with_missing_farm(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    create_response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    sensor_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sensors/{sensor_id}",
        json={
            "farm_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_update_sensor_with_missing_sensor_type(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    create_response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    sensor_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/sensors/{sensor_id}",
        json={
            "sensor_type_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found."


def test_delete_sensor(client):
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    create_response = client.post(
        "/api/v1/sensors",
        json=create_sensor_payload(
            farm_id,
            sensor_type_id,
        ),
    )

    sensor_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/sensors/{sensor_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/sensors/{sensor_id}")

    assert get_response.status_code == 404


def test_delete_sensor_not_found(client):
    response = client.delete("/api/v1/sensors/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor not found."
