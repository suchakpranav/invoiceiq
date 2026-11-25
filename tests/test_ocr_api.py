from fastapi.testclient import TestClient

from app.main import create_app
from app.services.ocr import OCRResult
from tests.test_storage import png


def test_ocr_lifecycle(db_settings, monkeypatch):
    monkeypatch.setattr('app.api.ocr.recognize', lambda *args: OCRResult(
        text='Invoice 123', words=[], mean_confidence=None))
    with TestClient(create_app(db_settings)) as client:
        upload = client.post('/api/v1/documents', files={'file': ('invoice.png', png())})
        assert upload.status_code == 201
        path = '/api/v1/documents/' + upload.json()['id']
        assert client.post(path + '/ocr').status_code == 409
        assert client.post(path + '/process').status_code == 200
        response = client.post(path + '/ocr')
        assert response.status_code == 200
        assert response.json()[0]['text'] == 'Invoice 123'
        assert client.get(path + '/ocr').json() == response.json()
        assert client.post(path + '/process').status_code == 200
        assert client.get(path + '/ocr').json() == []
