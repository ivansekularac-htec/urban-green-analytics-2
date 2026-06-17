def test_create_user_role(client):
    response = client.post(
        "/api/v1/user_role/",
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


def test_get_user_role(client):
    response = client.get("/api/v1/user_role/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_user_role(client):
    create = client.post(
        "/api/v1/user_role/",
        json={
            "user_id": 1,
            "role_id": 1,
            "farm_id": 1,
        },
    )
    user_role_id = create.json()["id"]

    response = client.put(
        f"/api/v1/user_role/{user_role_id}",
        json={
            "user_id": 2,
            "role_id": 2,
            "farm_id": 2,
        },
    )

    assert response.status_code == 200
    assert response.json()["user_id"] == 2


def test_delete_user_role(client):
    response = client.delete(
        "/api/v1/user-role/999999",
    )

    assert response.status_code == 404
