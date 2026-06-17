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


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_role(client):
    response = client.post(
        "/api/v1/roles/",
        json={
            "name": "Admin",
            "description": "System administrator",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Admin"
    assert data["description"] == "System administrator"


def test_create_role_invalid_payload(client):
    response = client.post(
        "/api/v1/roles/",
        json={},
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_roles(client):
    create_role(client)

    response = client.get("/api/v1/roles/")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_role_by_id(client):
    role = create_role(client)

    response = client.get(f"/api/v1/roles/{role['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == role["id"]


def test_get_role_not_found(client):
    response = client.get("/api/v1/roles/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_role(client):
    role = create_role(client)

    response = client.put(
        f"/api/v1/roles/{role['id']}",
        json={
            "name": "Super Admin",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Super Admin"


def test_update_role_duplicate_name(client):
    client.post(
        "/api/v1/roles/",
        json={
            "name": "Admin",
        },
    )

    second = client.post(
        "/api/v1/roles/",
        json={
            "name": "Operator",
        },
    ).json()

    response = client.put(
        f"/api/v1/roles/{second['id']}",
        json={
            "name": "Admin",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Role with this name already exists"


def test_update_role_not_found(client):
    response = client.put(
        "/api/v1/roles/9999",
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_role(client):
    role = create_role(client)

    response = client.delete(f"/api/v1/roles/{role['id']}")

    assert response.status_code == 204


def test_delete_role_not_found(client):
    response = client.delete("/api/v1/roles/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Role not found"
