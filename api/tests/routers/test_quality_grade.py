# ------------------------------------------------------
# CREATE
# ------------------------------------------------------


def test_create_quality_grade(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "Premium",
            "description": "Highest quality",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["code"] == "A"
    assert data["name"] == "Premium"
    assert data["description"] == "Highest quality"
    assert "id" in data


def test_create_duplicate_quality_grade_code(client):
    payload = {
        "code": "A",
        "name": "Premium",
    }

    client.post("/api/v1/quality-grades", json=payload)

    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "Different",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Quality grade with this code already exists")


def test_create_quality_grade_invalid_payload(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
        },
    )

    assert response.status_code == 422


def test_create_quality_grade_too_long_code(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A" * 51,
            "name": "Premium",
        },
    )

    assert response.status_code == 422


def test_create_quality_grade_too_long_name(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "X" * 101,
        },
    )

    assert response.status_code == 422


def test_create_quality_grade_too_long_description(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "Premium",
            "description": "X" * 501,
        },
    )

    assert response.status_code == 422


# ------------------------------------------------------
# READ
# ------------------------------------------------------


def create_grade(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "Premium",
        },
    )

    assert response.status_code == 201

    return response.json()


def test_get_all_quality_grades(client):
    create_grade(client)

    response = client.get("/api/v1/quality-grades")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_quality_grade_by_id(client):
    grade = create_grade(client)

    response = client.get(f"/api/v1/quality-grades/{grade['id']}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == grade["id"]


def test_get_quality_grade_not_found(client):
    response = client.get("/api/v1/quality-grades/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found"


# ------------------------------------------------------
# UPDATE
# ------------------------------------------------------


def test_update_quality_grade(client):
    grade = create_grade(client)

    response = client.put(
        f"/api/v1/quality-grades/{grade['id']}",
        json={
            "code": "B",
            "name": "Standard",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["code"] == "B"
    assert data["name"] == "Standard"


def test_update_quality_grade_duplicate_code(client):
    client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "Premium",
        },
    ).json()

    second = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "B",
            "name": "Standard",
        },
    ).json()

    response = client.put(
        f"/api/v1/quality-grades/{second['id']}",
        json={
            "code": "A",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == ("Quality grade with this code already exists")


def test_update_quality_grade_not_found(client):
    response = client.put(
        "/api/v1/quality-grades/999999",
        json={
            "name": "Updated",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found"


def test_partial_update_quality_grade(client):
    grade = create_grade(client)

    response = client.put(
        f"/api/v1/quality-grades/{grade['id']}",
        json={
            "name": "Updated Name",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Name"
    assert data["code"] == "A"


# ------------------------------------------------------
# DELETE
# ------------------------------------------------------


def test_delete_quality_grade(client):
    grade = create_grade(client)

    response = client.delete(f"/api/v1/quality-grades/{grade['id']}")

    assert response.status_code == 204

    response = client.get(f"/api/v1/quality-grades/{grade['id']}")

    assert response.status_code == 404


def test_delete_quality_grade_not_found(client):
    response = client.delete("/api/v1/quality-grades/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found"
