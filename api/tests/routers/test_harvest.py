import pytest


def create_farm(client):
    infra = client.post("/api/v1/infrastructure-types", json={"name": "Infra"}).json()
    system = client.post("/api/v1/growing-system-types", json={"name": "System"}).json()

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
        json={"name": "Wheat", "category_id": category["id"]},
    ).json()


def create_grade(client):
    r = client.post(
        "/api/v1/quality-grades",
        json={"code": "P", "name": "Premium", "description": "Premium quality"},
    )
    assert r.status_code == 201
    return r.json()


# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_harvest(client):
    farm = create_farm(client)
    crop = create_crop(client)
    grade = create_grade(client)

    r = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 100.5,
        },
    )

    assert r.status_code == 200 or r.status_code == 201
    data = r.json()

    assert "id" in data
    assert data["farm_id"] == farm["id"]
    assert data["crop_id"] == crop["id"]


def test_create_harvest_invalid_farm(client):
    crop = create_crop(client)
    grade = create_grade(client)

    r = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": 999999,
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 10,
        },
    )

    assert r.status_code == 404
    assert r.json()["detail"] == "Farm not found"


def test_create_harvest_invalid_crop(client):
    farm = create_farm(client)
    grade = create_grade(client)

    r = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": 999999,
            "quality_grade_id": grade["id"],
            "weight_kg": 10,
        },
    )

    assert r.status_code == 404
    assert r.json()["detail"] == "Crop not found"


def test_create_harvest_invalid_grade(client):
    farm = create_farm(client)
    crop = create_crop(client)

    r = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": 999999,
            "weight_kg": 10,
        },
    )

    assert r.status_code == 404
    assert r.json()["detail"] == "Quality grade not found"


def test_create_harvest_invalid_payload(client):
    r = client.post("/api/v1/harvests", json={})

    assert r.status_code == 422


def test_create_harvest_invalid_weight(client):
    farm = create_farm(client)
    crop = create_crop(client)
    grade = create_grade(client)

    r = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": -5,
        },
    )

    assert r.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_harvests(client):
    farm = create_farm(client)
    crop = create_crop(client)
    grade = create_grade(client)

    client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 10,
        },
    )

    client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 20,
        },
    )

    r = client.get("/api/v1/harvests")

    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_harvest_by_id(client):
    farm = create_farm(client)
    crop = create_crop(client)
    grade = create_grade(client)

    created = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 10,
        },
    ).json()

    r = client.get(f"/api/v1/harvests/{created['id']}")

    assert r.status_code == 200
    assert r.json()["id"] == created["id"]


def test_get_harvest_not_found(client):
    r = client.get("/api/v1/harvests/999999")

    assert r.status_code == 404
    assert r.json()["detail"] == "Harvest not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_harvest(client):
    farm = create_farm(client)
    crop = create_crop(client)
    grade = create_grade(client)

    created = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 10,
        },
    ).json()

    r = client.put(
        f"/api/v1/harvests/{created['id']}",
        json={"weight_kg": 50},
    )

    assert r.status_code == 200
    assert float(r.json()["weight_kg"]) == pytest.approx(50)


def test_update_harvest_invalid_grade(client):
    farm = create_farm(client)
    crop = create_crop(client)
    grade = create_grade(client)

    created = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 10,
        },
    ).json()

    r = client.put(
        f"/api/v1/harvests/{created['id']}",
        json={"quality_grade_id": 999999},
    )

    assert r.status_code == 404
    assert r.json()["detail"] == "Quality grade not found"


def test_update_harvest_not_found(client):
    r = client.put(
        "/api/v1/harvests/999999",
        json={"weight_kg": 10},
    )

    assert r.status_code == 404


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_harvest(client):
    farm = create_farm(client)
    crop = create_crop(client)
    grade = create_grade(client)

    created = client.post(
        "/api/v1/harvests",
        json={
            "farm_id": farm["id"],
            "crop_id": crop["id"],
            "quality_grade_id": grade["id"],
            "weight_kg": 10,
        },
    ).json()

    r = client.delete(f"/api/v1/harvests/{created['id']}")

    assert r.status_code == 405
