"""
Farm API tests.
"""

from uuid import uuid4


def create_infrastructure_type(client) -> int:
    """Create an infrastructure type test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/infrastructure-types",
        json={
            "name": f"Farm Infrastructure Dependency {suffix}",
            "description": "Farm infrastructure dependency",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def create_growing_system_type(client) -> int:
    """Create a growing system type test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": f"Farm Growing System Dependency {suffix}",
            "description": "Farm growing system dependency",
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_farm_crud(client):
    """Test farm CRUD endpoints."""
    suffix = uuid4().hex[:8]
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    create_response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_type_id,
            "growing_system_type_id": growing_system_type_id,
            "name": f"Test Farm {suffix}",
            "city": "Belgrade",
            "size_m2": 1250.5,
            "growing_beds_count": 24,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    farm_id = created["id"]

    list_response = client.get("/api/v1/farms")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/farms/{farm_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == farm_id

    update_response = client.put(
        f"/api/v1/farms/{farm_id}",
        json={"city": "Novi Sad"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["city"] == "Novi Sad"

    delete_response = client.delete(f"/api/v1/farms/{farm_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/farms/{farm_id}")
    assert missing_response.status_code == 404
