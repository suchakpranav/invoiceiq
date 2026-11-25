from fastapi.testclient import TestClient

from app.main import create_app
from tests.test_storage import png

URL = "/api/v1/documents"


def test_document_lifecycle(db_settings):
    with TestClient(create_app(db_settings)) as client:
        data = png()
        response = client.post(URL, files={"file": ("invoice.png", data, "image/png")})
        assert response.status_code == 201
        record = response.json()
        path = f"{URL}/{record['id']}"
        assert client.get(path).json() == record
        assert client.get(URL).json() == [record]
        assert client.get(path + "/download").content == data
        assert client.delete(path).status_code == 204
        assert client.get(path).status_code == 404
        assert not list(db_settings.upload_dir.iterdir())


def test_invalid_upload(db_settings):
    with TestClient(create_app(db_settings)) as client:
        assert client.post(URL, files={"file": ("fake.pdf", b"fake")}).status_code == 415
        assert client.get(URL).json() == []


def test_invoice_link_and_delete(db_settings):
    from tests.test_invoices import DATA

    with TestClient(create_app(db_settings)) as client:
        invoice = client.post("/api/v1/invoices", json=DATA).json()
        record = client.post(URL, files={"file": ("invoice.png", png())}).json()
        path = f"{URL}/{record['id']}"
        response = client.patch(path + "/invoice", json={"invoice_id": invoice["id"]})
        assert response.status_code == 200
        assert response.json()["invoice_id"] == invoice["id"]
        assert client.delete(f"/api/v1/invoices/{invoice['id']}").status_code == 204
        assert client.get(path).json()["invoice_id"] is None
