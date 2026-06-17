# ------------------------------------------------------
# helpers
# ------------------------------------------------------


def create_farm(client):
    infra = client.post("/api/v1/infrastructure-types", json={"name": "Infra A"}).json()

    system = client.post("/api/v1/growing-system-types", json={"name": "System A"}).json()

    return client.post(
        "/api/v1/farms",
        json={
            "name": "Farm A",
            "infrastructure_type_id": infra["id"],
            "growing_system_type_id": system["id"],
        },
    ).json()


def create_crop(client):
    category = client.post(
        "/api/v1/crop-categories",
        json={"name": "Grains"},
    ).json()

    return client.post(
        "/api/v1/crops",
        json={
            "name": "Wheat",
            "category_id": category["id"],
        },
    ).json()


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_farm_crop(client):
    farm = create_farm(client)
    crop = create_crop(client)

    response = client.post(
        "/api/v1/farm-crops",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "started_at": 20240001,
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["farm_id"] == farm["id"]
    assert data["crop_id"] == crop["id"]


def test_create_farm_crop_invalid_farm(client):
    crop = create_crop(client)

    response = client.post(
        "/api/v1/farm-crops",
        json={
            "farm_id": 999999,
            "crop_id": crop["id"],
            "started_at": 20240001,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Farm not found"


def test_create_farm_crop_invalid_crop(client):
    farm = create_farm(client)

    response = client.post(
        "/api/v1/farm-crops",
        json={
            "farm_id": farm["id"],
            "crop_id": 999999,
            "started_at": 20240001,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found"


def test_create_farm_crop_invalid_dates(client):
    farm = create_farm(client)
    crop = create_crop(client)

    response = client.post(
        "/api/v1/farm-crops",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "started_at": 20240010,
            "ended_at": 20240001,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "ended_at cannot be earlier than started_at"


def test_create_farm_crop_missing_fields(client):
    response = client.post(
        "/api/v1/farm-crops",
        json={"started_at": 20240001},
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_farm_crops(client):
    farm = create_farm(client)
    crop = create_crop(client)

    client.post(
        "/api/v1/farm-crops",
        json={"farm_id": farm["id"], "crop_id": crop["id"], "started_at": 1},
    )

    client.post(
        "/api/v1/farm-crops",
        json={"farm_id": farm["id"], "crop_id": crop["id"], "started_at": 2},
    )

    response = client.get("/api/v1/farm-crops")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_farm_crop_by_id(client):
    farm = create_farm(client)
    crop = create_crop(client)

    created = client.post(
        "/api/v1/farm-crops",
        json={"farm_id": farm["id"], "crop_id": crop["id"], "started_at": 1},
    ).json()

    response = client.get(f"/api/v1/farm-crops/{created['id']}")

    assert response.status_code == 200
    assert response.json()["farm_id"] == farm["id"]


def test_get_farm_crop_not_found(client):
    response = client.get("/api/v1/farm-crops/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "FarmCrop not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_farm_crop(client):
    farm = create_farm(client)
    crop = create_crop(client)

    created = client.post(
        "/api/v1/farm-crops",
        json={"farm_id": farm["id"], "crop_id": crop["id"], "started_at": 1},
    ).json()

    response = client.put(
        f"/api/v1/farm-crops/{created['id']}",
        json={"started_at": 10},
    )

    assert response.status_code == 200
    assert response.json()["started_at"] == 10


def test_update_farm_crop_not_found(client):
    response = client.put(
        "/api/v1/farm-crops/999999",
        json={"started_at": 10},
    )

    assert response.status_code == 404


def test_update_farm_crop_invalid_dates(client):
    farm = create_farm(client)
    crop = create_crop(client)

    created = client.post(
        "/api/v1/farm-crops",
        json={"farm_id": farm["id"], "crop_id": crop["id"], "started_at": 10},
    ).json()

    response = client.put(
        f"/api/v1/farm-crops/{created['id']}",
        json={
            "started_at": 20,
            "ended_at": 5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "ended_at cannot be earlier than started_at"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_farm_crop_not_allowed(client):
    response = client.delete("/api/v1/farm-crops/1")

    assert response.status_code == 405
