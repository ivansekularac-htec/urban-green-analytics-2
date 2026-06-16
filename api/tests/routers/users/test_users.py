"""
User API tests.
"""

from uuid import uuid4


def test_user_crud_hashes_password_and_hides_password_hash(client):
    """Test user CRUD endpoints with password handling."""
    suffix = uuid4().hex[:8]
    full_name = f"Test User {suffix}"

    create_response = client.post(
        "/api/v1/users",
        json={
            "email": f"test_user_{suffix}@example.com",
            "full_name": full_name,
            "password": "StrongPassword123",
        },
    )

    assert create_response.status_code == 201, create_response.json()
    created = create_response.json()
    user_id = created["id"]

    assert created["email"] == f"test_user_{suffix}@example.com"
    assert created["full_name"] == full_name
    assert created["is_active"] is True
    assert "password" not in created
    assert "password_hash" not in created

    list_response = client.get("/api/v1/users")
    assert list_response.status_code == 200
    assert isinstance(list_response.json(), list)

    get_response = client.get(f"/api/v1/users/{user_id}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == user_id
    assert "password" not in get_response.json()
    assert "password_hash" not in get_response.json()

    updated_full_name = f"Updated User {suffix}"

    update_response = client.put(
        f"/api/v1/users/{user_id}",
        json={
            "full_name": updated_full_name,
            "password": "NewStrongPassword123",
        },
    )

    assert update_response.status_code == 200, update_response.json()
    assert update_response.json()["full_name"] == updated_full_name
    assert "password" not in update_response.json()
    assert "password_hash" not in update_response.json()

    delete_response = client.delete(f"/api/v1/users/{user_id}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/api/v1/users/{user_id}")
    assert missing_response.status_code == 404
