import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def client(db_settings):
    settings = db_settings.model_copy(update={"app_version": "0.1.0"})
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def test_health(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "version": "0.1.0", "environment": "test"}


def test_home(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "InvoiceIQ" in response.text


def test_static_assets(client):
    for path in ("style.css", "app.js"):
        assert client.get(f"/static/{path}").status_code == 200


def test_unknown_route(client):
    assert client.get("/not-a-route").status_code == 404


def test_openapi(client):
    assert "/api/v1/health" in client.get("/openapi.json").json()["paths"]
