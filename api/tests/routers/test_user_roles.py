def test_get_user_roles(client):
    response = client.get("/api/v1/user-roles/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user_role(client):
    response = client.post(
        "/api/v1/user-roles/",
        json={
            "user_id": 1,
            "role_id": 1,
            "farm_id": 1,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["user_id"] == 1
    assert data["role_id"] == 1
    assert data["farm_id"] == 1


def test_create_user_role_invalid_payload(client):
    response = client.post(
        "/api/v1/user-roles/",
        json={},
    )

    assert response.status_code == 422


def test_update_user_role_not_found(client):
    response = client.put(
        "/api/v1/user-roles/999999",
        json={
            "role_id": 2,
        },
    )

    assert response.status_code == 404


def test_delete_user_role_not_found(client):
    response = client.delete(
        "/api/v1/user-roles/999999",
    )

    assert response.status_code == 404
