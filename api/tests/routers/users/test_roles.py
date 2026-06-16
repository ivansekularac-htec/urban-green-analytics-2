"""
Role API tests.
"""

from uuid import uuid4


def test_role_crud(client):
    """Test role CRUD endpoints."""
    suffix = uuid4().hex[:8]

    create_response = client.post(
        "/api/v1/roles",
        json={
            "name": f"Test Role {suffix}",
            "description": "Test role description",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    role_id = created["id"]

    list_response = client.get("/api/v1/roles")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/roles/{role_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == role_id

    update_response = client.put(
        f"/api/v1/roles/{role_id}",
        json={"name": f"Updated Role {suffix}"},
    )

    assert update_response.status_code == 200
    assert update_response.json()["name"] == f"Updated Role {suffix}"

    delete_response = client.delete(f"/api/v1/roles/{role_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/roles/{role_id}")
    assert missing_response.status_code == 404
