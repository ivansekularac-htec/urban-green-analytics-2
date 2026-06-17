# tests/routers/test_user.py


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


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_user(client):
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "password123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "john@example.com"
    assert data["full_name"] == "John Doe"
    assert data["is_active"] is True


def test_create_user_duplicate_email(client):
    create_user(client)

    response = client.post(
        "/api/v1/users/",
        json={
            "email": "john@example.com",
            "full_name": "Another User",
            "password": "password123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"


def test_create_user_invalid_payload(client):
    response = client.post(
        "/api/v1/users/",
        json={},
    )

    assert response.status_code == 422


def test_create_user_invalid_email(client):
    response = client.post(
        "/api/v1/users/",
        json={
            "email": "nije-email",
            "full_name": "John Doe",
            "password": "password123",
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_users(client):
    create_user(client)

    response = client.get("/api/v1/users/")

    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_user_by_id(client):
    user = create_user(client)

    response = client.get(
        f"/api/v1/users/{user['id']}",
    )

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]


def test_get_user_not_found(client):
    response = client.get("/api/v1/users/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_user(client):
    user = create_user(client)

    response = client.put(
        f"/api/v1/users/{user['id']}",
        json={
            "full_name": "Updated User",
            "is_active": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["full_name"] == "Updated User"
    assert data["is_active"] is False


def test_update_user_duplicate_email(client):
    client.post(
        "/api/v1/users/",
        json={
            "email": "first@example.com",
            "full_name": "First",
            "password": "password123",
        },
    )

    second = client.post(
        "/api/v1/users/",
        json={
            "email": "second@example.com",
            "full_name": "Second",
            "password": "password123",
        },
    ).json()

    response = client.put(
        f"/api/v1/users/{second['id']}",
        json={
            "email": "first@example.com",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "User with this email already exists"


def test_update_user_not_found(client):
    response = client.put(
        "/api/v1/users/9999",
        json={
            "full_name": "Updated",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_invalid_email(client):
    user = create_user(client)

    response = client.put(
        f"/api/v1/users/{user['id']}",
        json={
            "email": "nije-email",
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------
# PASSWORD UPDATE
# ------------------------------------------------------


def test_update_user_password(client):
    user = create_user(client)

    response = client.put(
        f"/api/v1/users/{user['id']}/password",
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 200
    assert response.json()["id"] == user["id"]


def test_update_user_password_not_found(client):
    response = client.put(
        "/api/v1/users/9999/password",
        json={
            "password": "newpassword123",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


def test_update_user_password_invalid_payload(client):
    user = create_user(client)

    response = client.put(
        f"/api/v1/users/{user['id']}/password",
        json={
            "password": "123",
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_user(client):
    user = create_user(client)

    response = client.delete(
        f"/api/v1/users/{user['id']}",
    )

    assert response.status_code == 204


def test_delete_user_not_found(client):
    response = client.delete("/api/v1/users/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"
