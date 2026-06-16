"""
User role API tests.
"""

from uuid import uuid4


def create_user(client) -> int:
    """Create a user test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/users",
        json={
            "email": f"user_role_user_{suffix}@example.com",
            "full_name": f"User Role User {suffix}",
            "password": "StrongPassword123",
        },
    )

    assert response.status_code == 201, response.json()
    return response.json()["id"]


def create_role(client, name_prefix: str = "User Role Dependency Role") -> int:
    """Create a role test dependency."""
    suffix = uuid4().hex[:8]

    response = client.post(
        "/api/v1/roles",
        json={
            "name": f"{name_prefix} {suffix}",
            "description": "User role dependency role",
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
            "name": f"User Role Infrastructure {suffix}",
            "description": "User role infrastructure dependency",
        },
    )

    growing_response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": f"User Role Growing System {suffix}",
            "description": "User role growing system dependency",
        },
    )

    assert infrastructure_response.status_code == 201
    assert growing_response.status_code == 201

    response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_response.json()["id"],
            "growing_system_type_id": growing_response.json()["id"],
            "name": f"User Role Farm Dependency {suffix}",
            "city": "Belgrade",
            "size_m2": 900,
            "growing_beds_count": 9,
        },
    )

    assert response.status_code == 201
    return response.json()["id"]


def test_user_role_crud(client):
    """Test user role CRUD endpoints."""
    user_id = create_user(client)
    role_id = create_role(client)
    updated_role_id = create_role(client, "Updated User Role Dependency Role")
    farm_id = create_farm(client)

    create_response = client.post(
        "/api/v1/user-roles",
        json={
            "user_id": user_id,
            "role_id": role_id,
            "farm_id": farm_id,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    user_role_id = created["id"]

    list_response = client.get("/api/v1/user-roles")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/user-roles/{user_role_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == user_role_id

    update_response = client.put(
        f"/api/v1/user-roles/{user_role_id}",
        json={"role_id": updated_role_id},
    )

    assert update_response.status_code == 200
    assert update_response.json()["role_id"] == updated_role_id

    delete_response = client.delete(f"/api/v1/user-roles/{user_role_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/user-roles/{user_role_id}")
    assert missing_response.status_code == 404
