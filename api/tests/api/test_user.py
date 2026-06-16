"""
test_users.py
Tests for user CRUD endpoints.
"""


def test_create_user(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "is_active": True,
            "password": "password123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert data["is_active"] is True
    assert "id" in data
    assert "password" not in data
    assert "password_hash" not in data


def test_create_user_invalid_email(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "invalid-email",
            "full_name": "Test User",
            "is_active": True,
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_create_user_password_too_short(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "short-password@example.com",
            "full_name": "Test User",
            "is_active": True,
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_create_user_missing_required_fields(client):
    response = client.post(
        "/api/v1/users",
        json={
            "password": "password123",
        },
    )

    assert response.status_code == 422


def test_get_users(client):
    client.post(
        "/api/v1/users",
        json={
            "email": "list@example.com",
            "full_name": "List User",
            "is_active": True,
            "password": "password123",
        },
    )

    response = client.get("/api/v1/users")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "list@example.com"
    assert "password" not in data[0]
    assert "password_hash" not in data[0]


def test_get_user(client):
    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "get@example.com",
            "full_name": "Get User",
            "is_active": True,
            "password": "password123",
        },
    )

    user_id = create_response.json()["id"]

    response = client.get(f"/api/v1/users/{user_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["email"] == "get@example.com"
    assert data["full_name"] == "Get User"


def test_get_user_not_found(client):
    response = client.get("/api/v1/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_update_user(client):
    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "old@example.com",
            "full_name": "Old User",
            "is_active": True,
            "password": "password123",
        },
    )

    user_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/users/{user_id}",
        json={
            "email": "updated@example.com",
            "full_name": "Updated User",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["email"] == "updated@example.com"
    assert data["full_name"] == "Updated User"
    assert data["is_active"] is False
    assert "password_hash" not in data


def test_update_user_partial(client):
    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "partial@example.com",
            "full_name": "Partial User",
            "is_active": True,
            "password": "password123",
        },
    )

    user_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/users/{user_id}",
        json={
            "full_name": "Partially Updated User",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "partial@example.com"
    assert data["full_name"] == "Partially Updated User"
    assert data["is_active"] is True


def test_update_user_not_found(client):
    response = client.put(
        "/api/v1/users/999",
        json={
            "email": "missing@example.com",
            "full_name": "Missing User",
            "is_active": True,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_update_user_invalid_email(client):
    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "valid@example.com",
            "full_name": "Valid User",
            "is_active": True,
            "password": "password123",
        },
    )

    user_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/users/{user_id}",
        json={
            "email": "not-an-email",
        },
    )

    assert response.status_code == 422


def test_update_user_password(client):
    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "password@example.com",
            "full_name": "Password User",
            "is_active": True,
            "password": "password123",
        },
    )

    user_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/users/{user_id}/password",
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == user_id
    assert data["email"] == "password@example.com"
    assert "password" not in data
    assert "password_hash" not in data


def test_update_user_password_too_short(client):
    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "shortupdate@example.com",
            "full_name": "Short Update User",
            "is_active": True,
            "password": "password123",
        },
    )

    user_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/users/{user_id}/password",
        json={
            "password": "short",
        },
    )

    assert response.status_code == 422


def test_update_user_password_not_found(client):
    response = client.put(
        "/api/v1/users/999/password",
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."


def test_delete_user(client):
    create_response = client.post(
        "/api/v1/users",
        json={
            "email": "delete@example.com",
            "full_name": "Delete User",
            "is_active": True,
            "password": "password123",
        },
    )

    user_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/users/{user_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/users/{user_id}")

    assert get_response.status_code == 404


def test_delete_user_not_found(client):
    response = client.delete("/api/v1/users/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found."
