"""Tests for /users/ endpoints."""

USER_PAYLOAD = {
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "securepassword",
}


def test_list_empty(client):
    r = client.get("/api/v1/users/")
    assert r.status_code == 200
    assert r.json() == []


def test_create(client):
    r = client.post("/api/v1/users/", json=USER_PAYLOAD)
    assert r.status_code == 201
    data = r.json()
    assert data["email"] == "test@example.com"
    assert data["full_name"] == "Test User"
    assert "password" not in data
    assert "password_hash" not in data


def test_create_password_too_short(client):
    payload = {**USER_PAYLOAD, "password": "short"}
    r = client.post("/api/v1/users/", json=payload)
    assert r.status_code == 422


def test_create_invalid_email(client):
    payload = {**USER_PAYLOAD, "email": "not-an-email"}
    r = client.post("/api/v1/users/", json=payload)
    assert r.status_code == 422


def test_get(client):
    created = client.post("/api/v1/users/", json=USER_PAYLOAD).json()
    r = client.get(f"/api/v1/users/{created['id']}")
    assert r.status_code == 200
    assert r.json()["email"] == "test@example.com"


def test_get_not_found(client):
    r = client.get("/api/v1/users/999")
    assert r.status_code == 404


def test_update(client):
    created = client.post("/api/v1/users/", json=USER_PAYLOAD).json()
    r = client.put(f"/api/v1/users/{created['id']}", json={"full_name": "Updated Name"})
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"


def test_update_password(client):
    import bcrypt

    from app.services.users import user as user_service
    from tests.conftest import TestingSessionLocal

    created = client.post("/api/v1/users/", json=USER_PAYLOAD).json()
    r = client.put(f"/api/v1/users/{created['id']}", json={"password": "newpassword123"})
    assert r.status_code == 200
    assert "password" not in r.json()
    assert "password_hash" not in r.json()
    # verify the stored hash verifies against the new password
    db = TestingSessionLocal()
    try:
        user = user_service.get_user(db, created["id"])
        assert bcrypt.checkpw(b"newpassword123", user.password_hash.encode())
    finally:
        db.close()


def test_update_not_found(client):
    r = client.put("/api/v1/users/999", json={"full_name": "X"})
    assert r.status_code == 404


def test_delete(client):
    created = client.post("/api/v1/users/", json=USER_PAYLOAD).json()
    r = client.delete(f"/api/v1/users/{created['id']}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/users/{created['id']}").status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/users/999")
    assert r.status_code == 404
