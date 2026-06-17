# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_crop(client):
    category = client.post(
        "/api/v1/crop-categories",
        json={"name": "Cereals"},
    ).json()

    response = client.post(
        "/api/v1/crops",
        json={
            "name": "Wheat",
            "description": "Winter wheat",
            "category_id": category["id"],
        },
    )

    assert response.status_code == 201
    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "Wheat"
    assert data["category_id"] == category["id"]


def test_create_crop_invalid_category(client):
    response = client.post(
        "/api/v1/crops",
        json={
            "name": "Corn",
            "category_id": 999999,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found"


def test_create_crop_missing_required_fields(client):
    response = client.post(
        "/api/v1/crops",
        json={
            "category_id": 1,
        },
    )

    assert response.status_code == 422


def test_create_crop_invalid_category_type(client):
    response = client.post(
        "/api/v1/crops",
        json={
            "name": "Wheat",
            "category_id": "not-an-int",
        },
    )

    assert response.status_code == 422


def test_create_crop_name_too_long(client):
    response = client.post(
        "/api/v1/crops",
        json={
            "name": "x" * 200,
            "category_id": 1,
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def test_get_all_crops(client):
    category = client.post(
        "/api/v1/crop-categories",
        json={"name": "Vegetables"},
    ).json()

    client.post(
        "/api/v1/crops",
        json={"name": "Carrot", "category_id": category["id"]},
    )

    client.post(
        "/api/v1/crops",
        json={"name": "Potato", "category_id": category["id"]},
    )

    response = client.get("/api/v1/crops")

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_crop_by_id(client):
    category = client.post(
        "/api/v1/crop-categories",
        json={"name": "Fruit"},
    ).json()

    created = client.post(
        "/api/v1/crops",
        json={"name": "Apple", "category_id": category["id"]},
    ).json()

    response = client.get(f"/api/v1/crops/{created['id']}")

    assert response.status_code == 200
    assert response.json()["name"] == "Apple"


def test_get_crop_not_found(client):
    response = client.get("/api/v1/crops/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_crop(client):
    category = client.post(
        "/api/v1/crop-categories",
        json={"name": "Grains"},
    ).json()

    created = client.post(
        "/api/v1/crops",
        json={"name": "Barley", "category_id": category["id"]},
    ).json()

    response = client.put(
        f"/api/v1/crops/{created['id']}",
        json={"name": "Updated Barley"},
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Barley"


def test_update_crop_not_found(client):
    response = client.put(
        "/api/v1/crops/999999",
        json={"name": "X"},
    )

    assert response.status_code == 404


def test_update_crop_invalid_category(client):
    category = client.post(
        "/api/v1/crop-categories",
        json={"name": "Legumes"},
    ).json()

    created = client.post(
        "/api/v1/crops",
        json={"name": "Pea", "category_id": category["id"]},
    ).json()

    response = client.put(
        f"/api/v1/crops/{created['id']}",
        json={"category_id": 999999},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Crop category not found"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_crop_not_found(client):
    response = client.delete("/api/v1/crops/999999")

    assert response.status_code == 404


def test_delete_crop(client):
    category = client.post(
        "/api/v1/crop-categories",
        json={"name": "Root"},
    ).json()

    created = client.post(
        "/api/v1/crops",
        json={"name": "Beetroot", "category_id": category["id"]},
    ).json()

    response = client.delete(f"/api/v1/crops/{created['id']}")

    assert response.status_code == 204

    check = client.get(f"/api/v1/crops/{created['id']}")
    assert check.status_code == 404
