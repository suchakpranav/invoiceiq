from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.schemas.document import Document


def test_uploaded_at_serializes_to_utc():
    document = Document(
        id=uuid4(), invoice_id=None, original_filename='invoice.pdf',
        content_type='application/pdf', size_bytes=100, sha256='a' * 64,
        uploaded_at=datetime(2026, 11, 26, 1, 10, 3, 328732,
                             tzinfo=timezone(timedelta(hours=5, minutes=30))),
    )
    assert document.model_dump(mode='json')['uploaded_at'] == '2026-11-25T19:40:03.328732Z'
