"""
Infrastructure type API tests.
"""

from uuid import uuid4


def test_infrastructure_type_crud(client):
    """Test infrastructure type CRUD endpoints."""
    suffix = uuid4().hex[:8]

    create_response = client.post(
        "/api/v1/infrastructure-types",
        json={
            "name": f"Test Infrastructure Type {suffix}",
            "description": "Test infrastructure type description",
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    infrastructure_type_id = created["id"]

    list_response = client.get("/api/v1/infrastructure-types")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/infrastructure-types/{infrastructure_type_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == infrastructure_type_id
    assert get_response.json()["name"] == f"Test Infrastructure Type {suffix}"

    update_response = client.put(
        f"/api/v1/infrastructure-types/{infrastructure_type_id}",
        json={
            "name": f"Updated Infrastructure Type {suffix}",
            "description": "Updated infrastructure type description",
        },
    )

    assert update_response.status_code == 200
    assert update_response.json()["id"] == infrastructure_type_id
    assert update_response.json()["name"] == f"Updated Infrastructure Type {suffix}"
    assert update_response.json()["description"] == "Updated infrastructure type description"

    delete_response = client.delete(f"/api/v1/infrastructure-types/{infrastructure_type_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/infrastructure-types/{infrastructure_type_id}")
    assert missing_response.status_code == 404
