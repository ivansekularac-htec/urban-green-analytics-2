"""
test_quality_grades.py
Tests for quality grade CRUD endpoints.
"""


def test_create_quality_grade(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "A",
            "name": "Grade A",
            "description": "Premium quality",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["code"] == "A"
    assert data["name"] == "Grade A"
    assert data["description"] == "Premium quality"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_quality_grade_invalid_input(client):
    response = client.post(
        "/api/v1/quality-grades",
        json={
            "description": "Missing required code and name",
        },
    )

    assert response.status_code == 422


def test_get_quality_grades(client):
    client.post(
        "/api/v1/quality-grades",
        json={
            "code": "B",
            "name": "Grade B",
            "description": "Standard quality",
        },
    )

    response = client.get("/api/v1/quality-grades")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["code"] == "B"
    assert data[0]["name"] == "Grade B"
    assert data[0]["description"] == "Standard quality"


def test_get_quality_grade(client):
    create_response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "C",
            "name": "Grade C",
            "description": "Commercial quality",
        },
    )

    quality_grade_id = create_response.json()["id"]

    response = client.get(f"/api/v1/quality-grades/{quality_grade_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == quality_grade_id
    assert data["code"] == "C"
    assert data["name"] == "Grade C"
    assert data["description"] == "Commercial quality"


def test_get_quality_grade_not_found(client):
    response = client.get("/api/v1/quality-grades/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found."


def test_update_quality_grade(client):
    create_response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "D",
            "name": "Old Grade",
            "description": "Old description",
        },
    )

    quality_grade_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/quality-grades/{quality_grade_id}",
        json={
            "code": "D",
            "name": "Updated Grade",
            "description": "Updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == quality_grade_id
    assert data["code"] == "D"
    assert data["name"] == "Updated Grade"
    assert data["description"] == "Updated description"


def test_update_quality_grade_partial(client):
    create_response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "E",
            "name": "Partial Grade",
            "description": "Original description",
        },
    )

    quality_grade_id = create_response.json()["id"]

    response = client.put(
        f"/api/v1/quality-grades/{quality_grade_id}",
        json={
            "description": "Partially updated description",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["code"] == "E"
    assert data["name"] == "Partial Grade"
    assert data["description"] == "Partially updated description"


def test_update_quality_grade_not_found(client):
    response = client.put(
        "/api/v1/quality-grades/999",
        json={
            "code": "Z",
            "name": "Missing Grade",
            "description": "Missing description",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found."


def test_delete_quality_grade(client):
    create_response = client.post(
        "/api/v1/quality-grades",
        json={
            "code": "DEL",
            "name": "Delete Grade",
            "description": "To be deleted",
        },
    )

    quality_grade_id = create_response.json()["id"]

    response = client.delete(f"/api/v1/quality-grades/{quality_grade_id}")

    assert response.status_code == 204

    get_response = client.get(f"/api/v1/quality-grades/{quality_grade_id}")

    assert get_response.status_code == 404


def test_delete_quality_grade_not_found(client):
    response = client.delete("/api/v1/quality-grades/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Quality grade not found."
