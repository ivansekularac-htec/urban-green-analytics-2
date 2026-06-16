def test_create_user(client):
    response = client.post(
        "/api/v1/user/",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "strongpassword123",
            "is_active": True,
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "test@example.com"
    assert "id" in data


def test_get_user(client):
    # create first
    create = client.post(
        "/api/v1/user/",
        json={
            "email": "get@example.com",
            "full_name": "Get User",
            "password": "strongpassword123",
        },
    )
    user_id = create.json()["id"]

    # fetch
    response = client.get(f"/api/v1/user/{user_id}")

    assert response.status_code == 200
    assert response.json()["email"] == "get@example.com"


def test_update_user(client):
    create = client.post(
        "/api/v1/user/",
        json={
            "email": "update@example.com",
            "full_name": "Old Name",
            "password": "strongpassword123",
        },
    )
    user_id = create.json()["id"]

    response = client.put(
        f"/api/v1/user/{user_id}",
        json={"email": "update@example.com", "full_name": "New Name", "is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["full_name"] == "New Name"


def test_delete_user(client):
    create = client.post(
        "/api/v1/user/",
        json={
            "email": "delete@example.com",
            "full_name": "Delete Me",
            "password": "strongpassword123",
        },
    )
    user_id = create.json()["id"]

    response = client.delete(f"/api/v1/user/{user_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/user/{user_id}")
    assert get_response.status_code == 404
