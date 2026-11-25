from io import BytesIO

import pytest
from PIL import Image
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

from app.services.processing import ProcessingError, prepare_document


def digital_pdf(path):
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=200)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'):
        DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 18 Tf 20 100 Td (Invoice 123) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    writer.write(path)


def test_digital_pdf(tmp_path):
    path = tmp_path / 'digital.pdf'
    digital_pdf(path)
    page, = prepare_document(path, 'application/pdf')
    assert page.method == 'embedded_text'
    assert page.extracted_text == 'Invoice 123'
    assert page.image_png is None


def test_scanned_pdf(tmp_path):
    path = tmp_path / 'scan.pdf'
    Image.new('RGB', (300, 400), 'white').save(path)
    page, = prepare_document(path, 'application/pdf')
    assert page.method == 'ocr_required'
    assert page.extracted_text == ''
    with Image.open(BytesIO(page.image_png)) as image:
        assert image.mode == '1'


def test_image_resize(tmp_path):
    path = tmp_path / 'large.png'
    Image.new('RGB', (3000, 1000), 'white').save(path)
    page, = prepare_document(path, 'image/png')
    assert (page.width, page.height) == (2400, 800)


def test_page_limit(tmp_path):
    path = tmp_path / 'long.pdf'
    writer = PdfWriter()
    for _ in range(21):
        writer.add_blank_page(width=100, height=100)
    writer.write(path)
    with pytest.raises(ProcessingError, match='20 pages'):
        prepare_document(path, 'application/pdf')
