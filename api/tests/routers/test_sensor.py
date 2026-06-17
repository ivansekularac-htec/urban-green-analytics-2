def create_farm(client):
    infrastructure_type = client.post(
        "/api/v1/infrastructure-types",
        json={
            "name": "Greenhouse",
        },
    ).json()

    growing_system_type = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Hydroponic",
        },
    ).json()

    response = client.post(
        "/api/v1/farms",
        json={
            "name": "Test Farm",
            "location": "Belgrade",
            "size_m2": 1000,
            "infrastructure_type_id": infrastructure_type["id"],
            "growing_system_type_id": growing_system_type["id"],
        },
    )

    assert response.status_code == 201

    return response.json()


def create_sensor_type(client):
    r = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
            "unit": "C",
        },
    )

    assert r.status_code == 201
    return r.json()


def create_sensor(
    client,
    farm_id,
    sensor_type_id,
    serial_number="SN-001",
):
    response = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm_id,
            "sensor_type_id": sensor_type_id,
            "serial_number": serial_number,
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201

    return response.json()


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_sensor(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    response = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm["id"],
            "sensor_type_id": sensor_type["id"],
            "serial_number": "SN-001",
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["farm_id"] == farm["id"]
    assert data["sensor_type_id"] == sensor_type["id"]
    assert data["serial_number"] == "SN-001"
    assert data["status"] == "ACTIVE"


def test_create_sensor_invalid_farm(client):
    sensor_type = create_sensor_type(client)

    response = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": 9999,
            "sensor_type_id": sensor_type["id"],
            "serial_number": "SN-001",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_create_sensor_invalid_sensor_type(client):
    farm = create_farm(client)

    response = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm["id"],
            "sensor_type_id": 9999,
            "serial_number": "SN-001",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found"


def test_create_sensor_duplicate_serial_number(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm["id"],
            "sensor_type_id": sensor_type["id"],
            "serial_number": "SN-001",
        },
    )

    response = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm["id"],
            "sensor_type_id": sensor_type["id"],
            "serial_number": "SN-001",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Sensor with this serial number already exists")


def test_create_sensor_invalid_payload(client):
    response = client.post(
        "/api/v1/sensors",
        json={},
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_sensors(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    create_sensor(
        client,
        farm["id"],
        sensor_type["id"],
        "SN-001",
    )

    response = client.get("/api/v1/sensors")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_sensor_by_id(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    sensor = create_sensor(
        client,
        farm["id"],
        sensor_type["id"],
    )

    response = client.get(f"/api/v1/sensors/{sensor['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == sensor["id"]


def test_get_sensor_not_found(client):
    response = client.get("/api/v1/sensors/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_sensor(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    sensor = create_sensor(
        client,
        farm["id"],
        sensor_type["id"],
    )

    response = client.put(
        f"/api/v1/sensors/{sensor['id']}",
        json={
            "serial_number": "SN-999",
        },
    )

    assert response.status_code == 200
    assert response.json()["serial_number"] == "SN-999"


def test_update_sensor_invalid_farm(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    sensor = create_sensor(
        client,
        farm["id"],
        sensor_type["id"],
    )

    response = client.put(
        f"/api/v1/sensors/{sensor['id']}",
        json={
            "farm_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_update_sensor_invalid_sensor_type(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    sensor = create_sensor(
        client,
        farm["id"],
        sensor_type["id"],
    )

    response = client.put(
        f"/api/v1/sensors/{sensor['id']}",
        json={
            "sensor_type_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found"


def test_update_sensor_duplicate_serial_number(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    first = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm["id"],
            "sensor_type_id": sensor_type["id"],
            "serial_number": "SN-001",
        },
    ).json()

    second = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm["id"],
            "sensor_type_id": sensor_type["id"],
            "serial_number": "SN-002",
        },
    ).json()

    response = client.put(
        f"/api/v1/sensors/{second['id']}",
        json={
            "serial_number": first["serial_number"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Sensor with this serial number already exists")


def test_update_sensor_not_found(client):
    response = client.put(
        "/api/v1/sensors/9999",
        json={
            "serial_number": "SN-999",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor not found"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_sensor(client):
    farm = create_farm(client)
    sensor_type = create_sensor_type(client)

    sensor = create_sensor(
        client,
        farm["id"],
        sensor_type["id"],
    )

    response = client.delete(f"/api/v1/sensors/{sensor['id']}")

    assert response.status_code == 204


def test_delete_sensor_not_found(client):
    response = client.delete("/api/v1/sensors/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor not found"
