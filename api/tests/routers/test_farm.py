from app.models.farms.farm_status import FarmStatus


def create_infrastructure_type(client):
    return client.post(
        "/api/v1/infrastructure-types",
        json={"name": "Greenhouse"},
    ).json()


def create_growing_system_type(client):
    return client.post(
        "/api/v1/growing-system-types",
        json={"name": "Hydroponic"},
    ).json()


def create_farm_payload(client):
    infra = create_infrastructure_type(client)
    system = create_growing_system_type(client)

    return {
        "name": "Farm A",
        "infrastructure_type_id": infra["id"],
        "growing_system_type_id": system["id"],
    }


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_farm(client):
    payload = create_farm_payload(client)

    response = client.post("/api/v1/farms", json=payload)

    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "Farm A"
    assert data["infrastructure_type_id"] == payload["infrastructure_type_id"]
    assert data["growing_system_type_id"] == payload["growing_system_type_id"]
    assert data["status"] == FarmStatus.ACTIVE


def test_create_farm_missing_fields(client):
    response = client.post(
        "/api/v1/farms",
        json={"name": "Farm A"},
    )

    assert response.status_code == 422


def test_create_farm_invalid_infrastructure(client):
    system = create_growing_system_type(client)

    response = client.post(
        "/api/v1/farms",
        json={
            "name": "Farm A",
            "infrastructure_type_id": 999999,
            "growing_system_type_id": system["id"],
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Infrastructure type not found"


def test_create_farm_invalid_growing_system(client):
    infra = create_infrastructure_type(client)

    response = client.post(
        "/api/v1/farms",
        json={
            "name": "Farm A",
            "infrastructure_type_id": infra["id"],
            "growing_system_type_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Growing system type not found"


def test_create_farm_invalid_size_m2(client):
    payload = create_farm_payload(client)
    payload["size_m2"] = -100

    response = client.post(
        "/api/v1/farms",
        json=payload,
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_farms(client):
    payload = create_farm_payload(client)

    client.post("/api/v1/farms", json=payload)
    client.post("/api/v1/farms", json=payload)

    response = client.get("/api/v1/farms")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_farm_by_id(client):
    payload = create_farm_payload(client)

    created = client.post("/api/v1/farms", json=payload).json()

    response = client.get(f"/api/v1/farms/{created['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_get_farm_not_found(client):
    response = client.get("/api/v1/farms/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_farm(client):
    payload = create_farm_payload(client)

    created = client.post("/api/v1/farms", json=payload).json()

    response = client.put(
        f"/api/v1/farms/{created['id']}",
        json={"name": "Updated Farm"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Farm"


def test_update_farm_invalid_infrastructure(client):
    payload = create_farm_payload(client)

    created = client.post("/api/v1/farms", json=payload).json()

    response = client.put(
        f"/api/v1/farms/{created['id']}",
        json={"infrastructure_type_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Infrastructure type not found"


def test_update_farm_invalid_growing_system(client):
    payload = create_farm_payload(client)

    created = client.post("/api/v1/farms", json=payload).json()

    response = client.put(
        f"/api/v1/farms/{created['id']}",
        json={"growing_system_type_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Growing system type not found"


def test_update_farm_not_found(client):
    response = client.put(
        "/api/v1/farms/999999",
        json={"name": "X"},
    )

    assert response.status_code == 404


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_farm(client):
    payload = create_farm_payload(client)

    created = client.post("/api/v1/farms", json=payload).json()

    response = client.delete(f"/api/v1/farms/{created['id']}")

    assert response.status_code == 204

    check = client.get(f"/api/v1/farms/{created['id']}")
    assert check.status_code == 404
