def test_create_infrastructure_type(client):
    response = client.post(
        "/api/v1/infrastructure_type/",
        json={
            "name": "Greenhouse",
            "description": "Controlled environment structure",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Greenhouse"
    assert data["description"] == "Controlled environment structure"


def test_get_infrastructure_type(client):
    response = client.get("/api/v1/infrastructure_type/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
