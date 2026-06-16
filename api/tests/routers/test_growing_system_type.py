def test_get_growing_system_types(client):
    response = client.get("/api/v1/growing-system-types/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_growing_system_type(client):
    response = client.post(
        "/api/v1/growing-system-types/",
        json={
            "name": "Hydroponic",
            "description": "Growing plants without soil",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Hydroponic"
    assert data["description"] == "Growing plants without soil"


def test_create_growing_system_type_invalid_payload(client):
    response = client.post(
        "/api/v1/growing-system-types/",
        json={},
    )

    assert response.status_code == 422


def test_update_growing_system_type_not_found(client):
    response = client.put(
        "/api/v1/growing-system-types/999999",
        json={
            "name": "Updated System",
        },
    )

    assert response.status_code == 404
