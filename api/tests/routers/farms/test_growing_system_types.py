"""
Growing system type API tests.
"""

from uuid import uuid4


def test_growing_system_type_crud(client):
    """Test growing system type CRUD endpoints."""
    suffix = uuid4().hex[:8]

    create_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": f"Test Growing System Type {suffix}",
            "description": "Test growing system type description",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    growing_system_type_id = created["id"]

    list_response = client.get("/api/v1/growing-system-types")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/growing-system-types/{growing_system_type_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == growing_system_type_id

    update_response = client.put(
        f"/api/v1/growing-system-types/{growing_system_type_id}",
        json={"name": f"Updated Growing System Type {suffix}"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == f"Updated Growing System Type {suffix}"

    delete_response = client.delete(f"/api/v1/growing-system-types/{growing_system_type_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/growing-system-types/{growing_system_type_id}")
    assert missing_response.status_code == 404
