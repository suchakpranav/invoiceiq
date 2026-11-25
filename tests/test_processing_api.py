from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import ProcessedPageRow
from app.db.session import build_engine
from app.main import create_app
from tests.test_storage import png


def test_processing_lifecycle(db_settings):
    with TestClient(create_app(db_settings)) as client:
        record = client.post('/api/v1/documents', files={'file': ('invoice.png', png())})
        assert record.status_code == 201
        path = '/api/v1/documents/' + record.json()['id']
        assert client.get(path + '/pages').json() == []
        response = client.post(path + '/process')
        assert response.status_code == 200
        pages = response.json()
        assert pages[0]['method'] == 'ocr_required'
        assert client.post(path + '/process').json() == pages
        assert client.get(path + '/pages/1/image').content.startswith(b'\x89PNG')
    with TestClient(create_app(db_settings)) as client:
        assert client.get(path + '/pages').json() == pages
        assert client.delete(path).status_code == 204
        assert client.get(path + '/pages').status_code == 404
    engine = build_engine(db_settings.database_url)
    try:
        with engine.connect() as connection:
            assert connection.scalar(select(func.count()).select_from(ProcessedPageRow)) == 0
    finally:
        engine.dispose()
