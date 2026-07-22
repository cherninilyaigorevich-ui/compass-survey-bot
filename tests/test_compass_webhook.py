from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_compass_webhook_accepts_json() -> None:
    payload = {
        "event": "message_created",
        "user_id": "test-user",
        "text": "Привет",
    }

    response = client.post(
        "/compass/webhook",
        json=payload,
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }
