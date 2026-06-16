"""
test_user_roles.py
Tests for user role CRUD endpoints.
"""


def create_user(client) -> int:
    response = client.post(
        "/api/v1/users",
        json={
            "email": "user-role@example.com",
            "full_name": "User Role Test",
            "is_active": True,
            "password": "password123",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_role(client) -> int:
    response = client.post(
        "/api/v1/roles",
        json={
            "name": "ADMIN",
            "description": "Administrator role",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_infrastructure_type(client) -> int:
    response = client.post(
        "/api/v1/farm-infrastructure-types",
        json={
            "name": "Hydroponic",
            "description": "Infrastructure",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_growing_system_type(client) -> int:
    response = client.post(
        "/api/v1/growing-system-types",
        json={
            "name": "Tower",
            "description": "Growing system",
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_farm(client) -> int:
    infrastructure_type_id = create_infrastructure_type(client)
    growing_system_type_id = create_growing_system_type(client)

    response = client.post(
        "/api/v1/farms",
        json={
            "infrastructure_type_id": infrastructure_type_id,
            "growing_system_type_id": growing_system_type_id,
            "name": "User Role Farm",
            "city": "Belgrade",
            "size_m2": "100.000",
            "status": "ACTIVE",
            "growing_beds_count": 10,
        },
    )

    assert response.status_code == 201

    return response.json()["id"]


def create_user_role_payload(
    user_id: int,
    role_id: int,
    farm_id: int | None = None,
) -> dict[str, object]:
    return {
        "user_id": user_id,
        "role_id": role_id,
        "farm_id": farm_id,
    }


def test_create_user_role_without_farm(client):
    user_id = create_user(client)
    role_id = create_role(client)

    response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user_id
    assert data["role_id"] == role_id
    assert data["farm_id"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_user_role_with_farm(client):
    user_id = create_user(client)
    role_id = create_role(client)
    farm_id = create_farm(client)

    response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
            farm_id,
        ),
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user_id
    assert data["role_id"] == role_id
    assert data["farm_id"] == farm_id


def test_create_user_role_invalid_input(client):
    response = client.post(
        "/api/v1/user-roles",
        json={},
    )

    assert response.status_code == 422


def test_create_user_role_with_missing_user(client):
    role_id = create_role(client)

    response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            999,
            role_id,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_create_user_role_with_missing_role(client):
    user_id = create_user(client)

    response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            999,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found."


def test_create_user_role_with_missing_farm(client):
    user_id = create_user(client)
    role_id = create_role(client)

    response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
            999,
        ),
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_get_user_roles(client):
    user_id = create_user(client)
    role_id = create_role(client)

    client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    response = client.get("/api/v1/user-roles")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["user_id"] == user_id
    assert data[0]["role_id"] == role_id


def test_get_user_role(client):
    user_id = create_user(client)
    role_id = create_role(client)

    create_response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    user_role_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/user-roles/{user_role_id}",
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_role_id
    assert data["user_id"] == user_id
    assert data["role_id"] == role_id


def test_get_user_role_not_found(client):
    response = client.get("/api/v1/user-roles/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User role not found."


def test_update_user_role(client):
    user_id = create_user(client)
    role_id = create_role(client)
    farm_id = create_farm(client)

    create_response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    user_role_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/user-roles/{user_role_id}",
        json={
            "farm_id": farm_id,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_role_id
    assert data["user_id"] == user_id
    assert data["role_id"] == role_id
    assert data["farm_id"] == farm_id


def test_update_user_role_not_found(client):
    response = client.put(
        "/api/v1/user-roles/999",
        json={
            "farm_id": None,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User role not found."


def test_update_user_role_with_missing_user(client):
    user_id = create_user(client)
    role_id = create_role(client)

    create_response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    user_role_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/user-roles/{user_role_id}",
        json={
            "user_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_update_user_role_with_missing_role(client):
    user_id = create_user(client)
    role_id = create_role(client)

    create_response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    user_role_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/user-roles/{user_role_id}",
        json={
            "role_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found."


def test_update_user_role_with_missing_farm(client):
    user_id = create_user(client)
    role_id = create_role(client)

    create_response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    user_role_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/user-roles/{user_role_id}",
        json={
            "farm_id": 999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found."


def test_delete_user_role(client):
    user_id = create_user(client)
    role_id = create_role(client)

    create_response = client.post(
        "/api/v1/user-roles",
        json=create_user_role_payload(
            user_id,
            role_id,
        ),
    )

    user_role_id = create_response.json()["id"]

    response = client.delete(
        f"/api/v1/user-roles/{user_role_id}",
    )

    assert response.status_code == 204

    get_response = client.get(
        f"/api/v1/user-roles/{user_role_id}",
    )

    assert get_response.status_code == 404


def test_delete_user_role_not_found(client):
    response = client.delete("/api/v1/user-roles/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User role not found."
