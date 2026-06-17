# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_infrastructure_type(client):
    r = client.post(
        "/api/v1/infrastructure-types",
        json={"name": "Hydroponic", "description": "Water based system"},
    )

    assert r.status_code == 201
    data = r.json()

    assert "id" in data
    assert data["name"] == "Hydroponic"


def test_create_duplicate_infrastructure_type(client):
    r1 = client.post(
        "/api/v1/infrastructure-types",
        json={"name": "Aeroponic"},
    )
    assert r1.status_code == 201

    r2 = client.post(
        "/api/v1/infrastructure-types",
        json={"name": "Aeroponic"},
    )

    assert r2.status_code == 400
    assert r2.json()["detail"] == "Infrastructure type with this name already exists"


def test_create_invalid_payload(client):
    r = client.post(
        "/api/v1/infrastructure-types",
        json={},
    )

    assert r.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_infrastructure_types(client):
    client.post("/api/v1/infrastructure-types", json={"name": "A"})
    client.post("/api/v1/infrastructure-types", json={"name": "B"})

    r = client.get("/api/v1/infrastructure-types")

    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_infrastructure_type_by_id(client):
    created = client.post(
        "/api/v1/infrastructure-types",
        json={"name": "Single"},
    ).json()

    r = client.get(f"/api/v1/infrastructure-types/{created['id']}")

    assert r.status_code == 200
    assert r.json()["name"] == "Single"


def test_get_infrastructure_type_not_found(client):
    r = client.get("/api/v1/infrastructure-types/999999")

    assert r.status_code == 404
    assert r.json()["detail"] == "Infrastructure type not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_infrastructure_type(client):
    created = client.post(
        "/api/v1/infrastructure-types",
        json={"name": "Old"},
    ).json()

    r = client.put(
        f"/api/v1/infrastructure-types/{created['id']}",
        json={"name": "New"},
    )

    assert r.status_code == 200
    assert r.json()["name"] == "New"


def test_update_duplicate_name(client):
    a = client.post("/api/v1/infrastructure-types", json={"name": "A"}).json()
    b = client.post("/api/v1/infrastructure-types", json={"name": "B"}).json()

    r = client.put(
        f"/api/v1/infrastructure-types/{b['id']}",
        json={"name": "A"},
    )

    assert r.status_code == 400
    assert r.json()["detail"] == "Infrastructure type with this name already exists"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_infrastructure_type(client):
    created = client.post(
        "/api/v1/infrastructure-types",
        json={"name": "DeleteMe"},
    ).json()

    r = client.delete(f"/api/v1/infrastructure-types/{created['id']}")
    assert r.status_code == 204

    check = client.get(f"/api/v1/infrastructure-types/{created['id']}")
    assert check.status_code == 404


def test_delete_not_found(client):
    r = client.delete("/api/v1/infrastructure-types/999999")
    assert r.status_code == 404
