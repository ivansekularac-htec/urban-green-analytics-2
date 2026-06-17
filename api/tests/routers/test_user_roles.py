def create_user(client):
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_role(client):
    response = client.post(
        "/api/v1/roles/",
        json={
            "name": "Admin",
            "description": "System administrator",
        },
    )

    assert response.status_code == 201

    return response.json()


def create_user_role(client):
    user = create_user(client)
    role = create_role(client)

    response = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": role["id"],
        },
    )

    assert response.status_code == 201

    return response.json()


def create_farm(client):
    infrastructure_type = client.post(
        "/api/v1/infrastructure-types",
        json={"name": "Greenhouse"},
    ).json()

    growing_system_type = client.post(
        "/api/v1/growing-system-types",
        json={"name": "Hydroponic"},
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

    print(response.status_code)
    print(response.json())

    return response.json()


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_user_role(client):
    user = create_user(client)
    role = create_role(client)

    response = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": role["id"],
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == user["id"]
    assert data["role_id"] == role["id"]
    assert data["farm_id"] is None


def test_create_user_role_invalid_user(client):
    role = create_role(client)

    response = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": 9999,
            "role_id": role["id"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_create_user_role_invalid_role(client):
    user = create_user(client)

    response = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found"


def test_create_user_role_invalid_farm(client):
    user = create_user(client)
    role = create_role(client)

    response = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": role["id"],
            "farm_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_create_user_role_duplicate_assignment(client):
    user = create_user(client)
    role = create_role(client)

    client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": role["id"],
        },
    )

    response = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": role["id"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already has this role assignment"


def test_create_user_role_invalid_payload(client):
    response = client.post(
        "/api/v1/user-roles/",
        json={},
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_user_roles(client):
    create_user_role(client)

    response = client.get("/api/v1/user-roles/")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_user_role_by_id(client):
    user_role = create_user_role(client)

    response = client.get(f"/api/v1/user-roles/{user_role['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == user_role["id"]


def test_get_user_role_not_found(client):
    response = client.get("/api/v1/user-roles/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User role not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_user_role(client):
    user_role = create_user_role(client)

    farm = create_farm(client)

    response = client.put(
        f"/api/v1/user-roles/{user_role['id']}",
        json={
            "farm_id": farm["id"],
        },
    )

    assert response.status_code == 200
    assert response.json()["farm_id"] == farm["id"]


def test_update_user_role_invalid_user(client):
    user_role = create_user_role(client)

    response = client.put(
        f"/api/v1/user-roles/{user_role['id']}",
        json={
            "user_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_role_invalid_role(client):
    user_role = create_user_role(client)

    response = client.put(
        f"/api/v1/user-roles/{user_role['id']}",
        json={
            "role_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found"


def test_update_user_role_invalid_farm(client):
    user_role = create_user_role(client)

    response = client.put(
        f"/api/v1/user-roles/{user_role['id']}",
        json={
            "farm_id": 9999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_update_user_role_duplicate_assignment(client):
    user = create_user(client)

    role_admin = client.post(
        "/api/v1/roles/",
        json={"name": "Admin"},
    ).json()

    role_operator = client.post(
        "/api/v1/roles/",
        json={"name": "Operator"},
    ).json()

    first = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": role_admin["id"],
        },
    ).json()

    second = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": user["id"],
            "role_id": role_operator["id"],
        },
    ).json()

    response = client.put(
        f"/api/v1/user-roles/{second['id']}",
        json={
            "role_id": role_admin["id"],
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User already has this role assignment"


def test_update_user_role_not_found(client):
    response = client.put(
        "/api/v1/user-roles/9999",
        json={
            "farm_id": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User role not found"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_user_role(client):
    user_role = create_user_role(client)

    response = client.delete(f"/api/v1/user-roles/{user_role['id']}")

    assert response.status_code == 204


def test_delete_user_role_not_found(client):
    response = client.delete("/api/v1/user-roles/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User role not found"
