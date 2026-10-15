from fastapi.testclient import TestClient
from app.main import app


def test_health():
    # The application lifespan requires a running MongoDB replica set.
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
