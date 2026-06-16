def test_create_growing_system_type(client):
    response = client.post(
        "/api/v1/growing_system_type/",
        json={
            "name": "Hydroponic",
            "description": "Growing plants without soil",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Hydroponic"
    assert data["description"] == "Growing plants without soil"


def test_get_growing_system_type(client):
    response = client.get("/api/v1/growing_system_type/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
