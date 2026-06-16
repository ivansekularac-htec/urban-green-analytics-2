def test_create_role(client):
    response = client.post(
        "/api/v1/role/",
        json={
            "name": "Admin",
            "description": "System administrator role",
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Admin"
    assert "id" in data


def test_get_role(client):
    create = client.post(
        "/api/v1/role/",
        json={
            "name": "Manager",
            "description": "Farm manager role",
        },
    )
    role_id = create.json()["id"]

    response = client.get(f"/api/v1/role/{role_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Manager"


def test_update_role(client):
    create = client.post(
        "/api/v1/role/",
        json={
            "name": "Worker",
            "description": "Basic worker role",
        },
    )
    role_id = create.json()["id"]

    response = client.put(
        f"/api/v1/role/{role_id}",
        json={
            "name": "Senior Worker",
            "description": "Updated role",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Senior Worker"


def test_delete_role(client):
    create = client.post(
        "/api/v1/role/",
        json={
            "name": "Temp Role",
            "description": "To be deleted",
        },
    )
    role_id = create.json()["id"]

    response = client.delete(f"/api/v1/role/{role_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/role/{role_id}")
    assert get_response.status_code == 404
