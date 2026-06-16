"""
Sensor type API tests.
"""

from uuid import uuid4


def test_sensor_type_crud(client):
    """Test sensor type CRUD endpoints."""
    suffix = uuid4().hex[:8]

    create_response = client.post(
        "/api/v1/sensor-types",
        json={
            "name": f"Test Sensor Type {suffix}",
            "unit": "C",
            "optimal_min": 10,
            "optimal_max": 30,
            "description": "Test sensor type description",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    sensor_type_id = created["id"]

    list_response = client.get("/api/v1/sensor-types")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/sensor-types/{sensor_type_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == sensor_type_id

    update_response = client.put(
        f"/api/v1/sensor-types/{sensor_type_id}",
        json={"name": f"Updated Sensor Type {suffix}"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == f"Updated Sensor Type {suffix}"

    delete_response = client.delete(f"/api/v1/sensor-types/{sensor_type_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/sensor-types/{sensor_type_id}")
    assert missing_response.status_code == 404
