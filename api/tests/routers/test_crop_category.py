# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_crop_category(client):
    response = client.post(
        "/api/v1/crop-categories",
        json={"name": "Fruit", "description": "Fresh fruits"},
    )

    assert response.status_code == 201
    data = response.json()

    assert "id" in data
    assert data["name"] == "Fruit"


def test_create_duplicate_crop_category(client):
    r1 = client.post("/api/v1/crop-categories", json={"name": "Vegetable"})
    assert r1.status_code == 201

    r2 = client.post("/api/v1/crop-categories", json={"name": "Vegetable"})

    assert r2.status_code == 409
    assert r2.json()["detail"] == "Crop category with this name already exists"


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_crop_categories(client):
    client.post("/api/v1/crop-categories", json={"name": "A"})
    client.post("/api/v1/crop-categories", json={"name": "B"})

    response = client.get("/api/v1/crop-categories")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2


def test_get_crop_category_by_id(client):
    created = client.post(
        "/api/v1/crop-categories",
        json={"name": "Single"},
    )

    assert created.status_code == 201
    created_id = created.json()["id"]

    response = client.get(f"/api/v1/crop-categories/{created_id}")

    assert response.status_code == 200
    assert response.json()["name"] == "Single"


def test_get_crop_category_not_found(client):
    response = client.get("/api/v1/crop-categories/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_crop_category(client):
    created = client.post(
        "/api/v1/crop-categories",
        json={"name": "Old"},
    )

    assert created.status_code == 201
    created_id = created.json()["id"]

    response = client.put(
        f"/api/v1/crop-categories/{created_id}",
        json={"name": "New"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "New"


def test_update_not_found(client):
    response = client.put(
        "/api/v1/crop-categories/999999",
        json={"name": "X"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found"


def test_update_conflict_name(client):
    client.post("/api/v1/crop-categories", json={"name": "A"})
    b = client.post("/api/v1/crop-categories", json={"name": "B"}).json()

    response = client.put(
        f"/api/v1/crop-categories/{b['id']}",
        json={"name": "A"},
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Crop category name already exists"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_crop_category(client):
    created = client.post(
        "/api/v1/crop-categories",
        json={"name": "ToDelete"},
    )

    assert created.status_code == 201
    created_id = created.json()["id"]

    response = client.delete(f"/api/v1/crop-categories/{created_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/crop-categories/{created_id}")
    assert get_response.status_code == 404


def test_delete_not_found(client):
    response = client.delete("/api/v1/crop-categories/999999")

    assert response.status_code == 404


def test_create_validation_error(client):
    response = client.post(
        "/api/v1/crop-categories",
        json={"name": "A" * 200},
    )

    assert response.status_code == 422
