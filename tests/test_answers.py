from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_create_yes_answer():

    response = client.post(
        "/answers",
        json={
            "user_id": "test123",
            "username": "pytest",
            "answer": "Yes",
            "location": "SPB",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "yes"


def test_create_no_answer():

    response = client.post(
        "/answers",
        json={
            "user_id": "test124",
            "answer": "No",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["answer"] == "no"


def test_invalid_answer():

    response = client.post(
        "/answers",
        json={
            "user_id": "test125",
            "answer": "maybe",
        },
    )

    assert response.status_code == 422
