def test_get_sensors(client):
    response = client.get("/api/v1/sensors/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_sensor(client):
    response = client.post(
        "/api/v1/sensors/",
        json={
            "farm_id": 1,
            "sensor_type_id": 1,
            "serial_number": "SN-001",
            "status": "ACTIVE",
            "installed_at": 1781625767,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == 1
    assert data["sensor_type_id"] == 1
    assert data["serial_number"] == "SN-001"


def test_create_sensor_invalid_payload(client):
    response = client.post(
        "/api/v1/sensors/",
        json={},
    )

    assert response.status_code == 422


def test_update_sensor_not_found(client):
    response = client.put(
        "/api/v1/sensors/999999",
        json={
            "serial_number": "UPDATED-SN",
        },
    )

    assert response.status_code == 404
