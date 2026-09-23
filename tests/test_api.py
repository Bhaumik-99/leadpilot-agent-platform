from fastapi.testclient import TestClient

from app.api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_agent_endpoint():
    response = client.post("/v1/agent/respond", json={"message": "We need a CRM for 15 salespeople in Gurgaon", "channel": "web"})
    assert response.status_code == 200
    body = response.json()
    assert body["lead_id"].startswith("LD-")
    assert body["lead"]["team_size"] == 15
