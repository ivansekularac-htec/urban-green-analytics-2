"""
Sensor API tests.
"""

from uuid import uuid4


def create_sensor_type(client) -> int:
    """Create a sensor type test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": f"Sensor Dependency Type {suffix}",
            "unit": "C",
            "optimal_min": 10,
            "optimal_max": 30,
            "description": "Sensor type dependency",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_farm(client) -> int:
    """Create a farm test dependency."""
    suffix = uuid4().hex[:8]

    infrastructure_response = client.post(
        "/api/v1/infrastructure-types",
        json={
            "name": f"Sensor Infrastructure {suffix}",
            "description": "Sensor infrastructure dependency",
        },
    )

    growing_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": f"Sensor Growing System {suffix}",
            "description": "Sensor growing system dependency",
        },
    )

    assert infrastructure_response.status_code == 201
    assert growing_response.status_code == 201

    response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_response.json()["id"],
            "growing_system_type_id": growing_response.json()["id"],
            "name": f"Sensor Farm Dependency {suffix}",
            "city": "Belgrade",
            "size_m2": 500,
            "growing_beds_count": 5,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_sensor_crud(client):
    """Test sensor CRUD endpoints."""
    suffix = uuid4().hex[:8]
    farm_id = create_farm(client)
    sensor_type_id = create_sensor_type(client)

    create_response = client.post(
        "/api/v1/sensors",
        json={
            "farm_id": farm_id,
            "sensor_type_id": sensor_type_id,
            "serial_number": f"SN-{suffix}",
            "status": "ACTIVE",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    sensor_id = created["id"]

    list_response = client.get("/api/v1/sensors")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/sensors/{sensor_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == sensor_id

    update_response = client.put(
        f"/api/v1/sensors/{sensor_id}",
        json={"status": "MAINTENANCE"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["status"] == "MAINTENANCE"

    delete_response = client.delete(f"/api/v1/sensors/{sensor_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/sensors/{sensor_id}")
    assert missing_response.status_code == 404
