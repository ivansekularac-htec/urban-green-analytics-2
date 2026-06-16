def test_get_infrastructure_types(client):
    response = client.get("/api/v1/infrastructure-types/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_infrastructure_type(client):
    response = client.post(
        "/api/v1/infrastructure-types/",
        json={
            "name": "Greenhouse",
            "description": "Controlled environment structure",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Greenhouse"
    assert data["description"] == "Controlled environment structure"


def test_create_infrastructure_type_invalid_payload(client):
    response = client.post(
        "/api/v1/infrastructure-types/",
        json={},
    )

    assert response.status_code == 422


def test_update_infrastructure_type_not_found(client):
    response = client.put(
        "/api/v1/infrastructure-types/999999",
        json={
            "name": "Updated Infrastructure",
        },
    )

    assert response.status_code == 404
