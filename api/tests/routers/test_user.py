def test_get_users(client):
    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_user(client):
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "password123",
            "is_active": True,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"


def test_create_user_invalid_payload(client):
    response = client.post(
        "/api/v1/users/",
        json={},
    )

    assert response.status_code == 422


def test_update_user_not_found(client):
    response = client.put(
        "/api/v1/users/999999",
        json={
            "full_name": "Updated User",
        },
    )

    assert response.status_code == 404
