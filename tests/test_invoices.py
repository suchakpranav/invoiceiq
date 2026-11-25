from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import create_app

URL = "/api/v1/invoices"
DATA = {
    "invoice_number": "INV-001", "supplier": "Sample Traders", "customer": "Demo Retail",
    "invoice_date": "2026-11-25", "subtotal": "1250.50", "tax_rate": "18",
}


@pytest.fixture
def client(db_settings):
    with TestClient(create_app(db_settings)) as test_client:
        yield test_client


def test_crud(client):
    response = client.post(URL, json=DATA)
    assert response.status_code == 201
    record = response.json()
    assert record["tax_amount"] == "225.09"
    assert record["total"] == "1475.59"
    path = f'{URL}/{record["id"]}'
    assert client.get(path).json() == record
    updated = client.put(path, json={**DATA, "subtotal": "100"})
    assert updated.status_code == 200
    assert updated.json()["total"] == "118.00"
    assert client.delete(path).status_code == 204
    assert client.get(path).status_code == 404


@pytest.mark.parametrize("change", [
    {"subtotal": "-1"}, {"tax_rate": "101"}, {"supplier": "  "},
    {"invoice_date": "invalid"}, {"subtotal": "1.001"}, {"total": "1"},
])
def test_invalid_input(client, change):
    assert client.post(URL, json={**DATA, **change}).status_code == 422


def test_search_and_pagination(client):
    client.post(URL, json=DATA)
    client.post(URL, json={**DATA, "invoice_number": "INV-002", "supplier": "Other"})
    assert client.get(URL, params={"q": "sample"}).json()["total"] == 1
    assert client.get(URL, params={"supplier": "other"}).json()["total"] == 1
    page = client.get(URL, params={"limit": 1, "offset": 1}).json()
    assert page["total"] == 2 and len(page["items"]) == 1
    assert client.get(URL, params={"date_to": "2026-01-01"}).json()["total"] == 0
    assert client.get(URL, params={"limit": 0}).status_code == 422
    assert client.get(URL, params={
        "date_from": "2026-02-01", "date_to": "2026-01-01"
    }).status_code == 422


def test_missing_record(client):
    path = f"{URL}/{uuid4()}"
    assert client.get(path).status_code == 404
    assert client.put(path, json=DATA).status_code == 404
    assert client.delete(path).status_code == 404
    assert client.get(f"{URL}/invalid").status_code == 422


def test_rounding(client):
    record = client.post(URL, json={**DATA, "subtotal": "0.05", "tax_rate": "10"}).json()
    assert record["tax_amount"] == "0.01"


def test_app_isolation(client, isolated_database):
    client.post(URL, json=DATA)
    with TestClient(create_app(isolated_database())) as other:
        assert other.get(URL).json()["total"] == 0


def test_persistence(db_settings):
    with TestClient(create_app(db_settings)) as first:
        record = first.post(URL, json={**DATA, "notes": "Paid"}).json()
    with TestClient(create_app(db_settings)) as second:
        assert second.get(f"{URL}/{record['id']}").json() == record


def test_literal_search(client):
    client.post(URL, json=DATA)
    assert client.get(URL, params={"q": "%"}).json()["total"] == 0


def test_large_amount(client):
    record = client.post(URL, json={**DATA, "subtotal": "9999999999.99"}).json()
    assert client.get(f"{URL}/{record['id']}").json()["subtotal"] == "9999999999.99"
