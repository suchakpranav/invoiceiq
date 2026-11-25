from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfWriter

from app.services.storage import DocumentTooLarge, InvalidDocument, store_document


def png():
    stream = BytesIO()
    Image.new("RGB", (20, 20), "white").save(stream, format="PNG")
    return stream.getvalue()


def test_valid_png(tmp_path):
    data = png()
    name, key, media, size, digest = store_document(
        BytesIO(data), "../../invoice.png", tmp_path, 10000
    )
    assert name == "invoice.png"
    assert (tmp_path / key).read_bytes() == data
    assert media == "image/png" and size == len(data) and len(digest) == 64


def test_valid_pdf(tmp_path):
    stream = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.write(stream)
    stream.seek(0)
    assert store_document(stream, "invoice.pdf", tmp_path, 10000)[2] == "application/pdf"


@pytest.mark.parametrize("name,data", [("fake.png", b"fake"), ("empty.pdf", b""),
                                      ("script.exe", b"test"), ("fake.jpg", png())])
def test_invalid(tmp_path, name, data):
    with pytest.raises(InvalidDocument):
        store_document(BytesIO(data), name, tmp_path, 10000)
    assert not list(tmp_path.iterdir())


def test_limit(tmp_path):
    with pytest.raises(DocumentTooLarge):
        store_document(BytesIO(png()), "invoice.png", tmp_path, 1)
    assert not list(tmp_path.iterdir())
