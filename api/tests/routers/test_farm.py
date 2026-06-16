def test_create_farm(client):
    response = client.post(
        "/api/v1/farm/",
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


def test_get_farm(client):
    response = client.get("/api/v1/farm/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_update_farm(client):
    create = client.post(
        "/api/v1/farm/",
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
    farm_id = create.json()["id"]

    response = client.put(
        f"/api/v1/farm/{farm_id}",
        json={
            "name": "Updated Farm",
            "city": "Belgrade",
            "size_m2": "100.50",
            "growing_beds_count": 10,
            "infrastructure_type_id": 1,
            "growing_system_type_id": 1,
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Farm"


def test_delete_farm(client):
    create = client.post(
        "/api/v1/farm/",
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
    farm_id = create.json()["id"]

    response = client.delete(f"/api/v1/farm/{farm_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/farm/{farm_id}")
    assert get_response.status_code == 404
