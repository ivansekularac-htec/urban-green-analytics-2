def test_get_roles(client):
    response = client.get("/api/v1/roles/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


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


def test_update_role_not_found(client):
    response = client.put(
        "/api/v1/roles/999999",
        json={
            "name": "Updated Role",
        },
    )

    assert response.status_code == 404
