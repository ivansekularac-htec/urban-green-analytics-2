def test_create_sensor(client):
    response = client.post(
        "/api/v1/sensor/",
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


def test_get_sensor(client):
    response = client.get("/api/v1/sensor/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
