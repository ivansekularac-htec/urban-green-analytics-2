def create_sensor_type(
    client,
    name="Temperature",
    unit="°C",
    description="Temperature sensor",
    optimal_min=18,
    optimal_max=30,
):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": name,
            "unit": unit,
            "description": description,
            "optimal_min": optimal_min,
            "optimal_max": optimal_max,
        },
    )

    assert response.status_code == 201

    return response.json()


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_sensor_type(client):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
            "unit": "°C",
            "description": "Temperature sensor",
            "optimal_min": 18,
            "optimal_max": 30,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Temperature"
    assert data["unit"] == "°C"


def test_create_duplicate_sensor_type_name(client):
    create_sensor_type(client)

    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
            "unit": "%",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Sensor type with this name already exists")


def test_create_sensor_type_invalid_range(client):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
            "unit": "°C",
            "optimal_min": 50,
            "optimal_max": 10,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("optimal_min cannot be greater than optimal_max")


def test_create_sensor_type_invalid_payload(client):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
        },
    )

    assert response.status_code == 422


def test_create_sensor_type_name_too_long(client):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "X" * 101,
            "unit": "°C",
        },
    )

    assert response.status_code == 422


def test_create_sensor_type_unit_too_long(client):
    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": "Temperature",
            "unit": "X" * 51,
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_sensor_types(client):
    create_sensor_type(client)

    response = client.get("/api/v1/sensor-types")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_sensor_type_by_id(client):
    sensor_type = create_sensor_type(client)

    response = client.get(f"/api/v1/sensor-types/{sensor_type['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == sensor_type["id"]


def test_get_sensor_type_not_found(client):
    response = client.get("/api/v1/sensor-types/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_sensor_type(client):
    sensor_type = create_sensor_type(client)

    response = client.put(
        f"/api/v1/sensor-types/{sensor_type['id']}",
        json={
            "name": "Humidity",
            "unit": "%",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Humidity"
    assert data["unit"] == "%"


def test_partial_update_sensor_type(client):
    sensor_type = create_sensor_type(client)

    response = client.put(
        f"/api/v1/sensor-types/{sensor_type['id']}",
        json={
            "name": "Humidity",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Humidity"
    assert data["unit"] == "°C"


def test_update_sensor_type_duplicate_name(client):
    create_sensor_type(client)

    second = create_sensor_type(
        client,
        name="Humidity",
        unit="%",
    )

    response = client.put(
        f"/api/v1/sensor-types/{second['id']}",
        json={
            "name": "Temperature",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Sensor type with this name already exists")


def test_update_sensor_type_invalid_range(client):
    sensor_type = create_sensor_type(client)

    response = client.put(
        f"/api/v1/sensor-types/{sensor_type['id']}",
        json={
            "optimal_min": 100,
            "optimal_max": 10,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("optimal_min cannot be greater than optimal_max")


def test_update_sensor_type_not_found(client):
    response = client.put(
        "/api/v1/sensor-types/999999",
        json={
            "name": "Humidity",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found"


def test_update_sensor_type_partial_range_invalid(client):
    sensor_type = create_sensor_type(
        client,
        optimal_min=10,
        optimal_max=20,
    )

    response = client.put(
        f"/api/v1/sensor-types/{sensor_type['id']}",
        json={
            "optimal_min": 30,
        },
    )

    assert response.status_code == 400


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_sensor_type(client):
    sensor_type = create_sensor_type(client)

    response = client.delete(f"/api/v1/sensor-types/{sensor_type['id']}")

    assert response.status_code == 204

    response = client.get(f"/api/v1/sensor-types/{sensor_type['id']}")

    assert response.status_code == 404


def test_delete_sensor_type_not_found(client):
    response = client.delete("/api/v1/sensor-types/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Sensor type not found"
