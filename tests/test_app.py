from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app

client = TestClient(create_app(Settings(environment="test", app_version="0.1.0")))


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0", "environment": "test"}


def test_home():
    response = client.get("/")
    assert response.status_code == 200
    assert "InvoiceIQ" in response.text


def test_static_assets():
    for path in ("style.css", "app.js"):
        assert client.get(f"/static/{path}").status_code == 200


def test_unknown_route():
    assert client.get("/not-a-route").status_code == 404


def test_openapi():
    assert "/api/v1/health" in client.get("/openapi.json").json()["paths"]
