
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_get_leads():
    response = client.get("/leads")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
