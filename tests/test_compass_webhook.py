from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_compass_webhook_accepts_json() -> None:
    payload = {
        "group_id": "",
        "message_id": "test-message-1",
        "text": "/help",
        "type": "single",
        "user_id": 12345,
    }

    response = client.post(
        "/api/compass/webhook",
        json=payload,
        headers={
            "Authorization": f"Bearer {settings.compass_bot_token}",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["answer"]["action"] == "message_send"
    assert body["answer"]["post"]["type"] == "text"
    assert isinstance(body["answer"]["post"]["text"], str)
    assert body["answer"]["post"]["text"]
