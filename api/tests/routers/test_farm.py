def test_get_farms(client):
    response = client.get("/api/v1/farms/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_create_farm(client):
    response = client.post(
        "/api/v1/farms/",
        json={
            "name": "Test Farm",
            "city": "Belgrade",
            "size_m2": "100.50",
            "growing_beds_count": 10,
            "infrastructure_type_id": 1,
            "growing_system_type_id": 1,
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Test Farm"
    assert data["city"] == "Belgrade"


def test_create_farm_invalid_payload(client):
    response = client.post(
        "/api/v1/farms/",
        json={},
    )

    assert response.status_code == 422


def test_update_farm_not_found(client):
    response = client.put(
        "/api/v1/farms/999999",
        json={
            "name": "Updated Farm",
        },
    )

    assert response.status_code == 404
