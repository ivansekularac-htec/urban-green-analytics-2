# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_growing_system_type(client):
    r = client.post(
        "/api/v1/growing-system-types",
        json={"name": "Vertical Farming", "description": "Stacked systems"},
    )

    assert r.status_code == 201
    data = r.json()

    assert "id" in data
    assert data["name"] == "Vertical Farming"


def test_create_duplicate_growing_system_type(client):
    r1 = client.post(
        "/api/v1/growing-system-types",
        json={"name": "Vertical"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/v1/growing-system-types",
        json={"name": "Vertical"},
    )

    assert r2.status_code in (409, 400)


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_growing_system_types(client):
    client.post("/api/v1/growing-system-types", json={"name": "A"})
    client.post("/api/v1/growing-system-types", json={"name": "B"})

    r = client.get("/api/v1/growing-system-types")

    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_growing_system_type_by_id(client):
    created = client.post(
        "/api/v1/growing-system-types",
        json={"name": "Single"},
    ).json()

    r = client.get(f"/api/v1/growing-system-types/{created['id']}")

    assert r.status_code == 200
    assert r.json()["name"] == "Single"


def test_get_not_found(client):
    r = client.get("/api/v1/growing-system-types/999999")

    assert r.status_code == 404


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_growing_system_type(client):
    created = client.post(
        "/api/v1/growing-system-types",
        json={"name": "Old"},
    ).json()

    r = client.put(
        f"/api/v1/growing-system-types/{created['id']}",
        json={"name": "New"},
    )

    assert r.status_code == 200
    assert r.json()["name"] == "New"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_growing_system_type(client):
    created = client.post(
        "/api/v1/growing-system-types",
        json={"name": "DeleteMe"},
    ).json()

    r = client.delete(f"/api/v1/growing-system-types/{created['id']}")

    assert r.status_code == 204

    check = client.get(f"/api/v1/growing-system-types/{created['id']}")
    assert check.status_code == 404
