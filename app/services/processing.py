"""Bounded, synchronous document preparation; no OCR yet."""

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from threading import Lock

import pypdfium2 as pdfium
from PIL import Image, ImageFilter, ImageOps

MAX_PAGES = 20
MAX_SIDE = 2400
MAX_TEXT = 100_000
MAX_IMAGE_BYTES = 2_000_000
PDF_LOCK = Lock()  # PDFium is not thread-safe, even across different documents.


class ProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class PreparedPage:
    page_number: int
    method: str
    extracted_text: str
    image_png: bytes | None = None
    width: int | None = None
    height: int | None = None


def prepare_image(image: Image.Image, number: int) -> PreparedPage:
    image = ImageOps.exif_transpose(image)
    image.thumbnail((MAX_SIDE, MAX_SIDE), Image.Resampling.LANCZOS)
    rgba = image.convert("RGBA")
    white = Image.new("RGBA", rgba.size, "white")
    white.alpha_composite(rgba)
    gray = ImageOps.autocontrast(white.convert("L"))
    gray = gray.filter(ImageFilter.MedianFilter(3))
    binary = gray.point(lambda pixel: 255 if pixel >= 160 else 0, mode="1")
    output = BytesIO()
    binary.save(output, format="PNG")
    data = output.getvalue()
    if len(data) > MAX_IMAGE_BYTES:
        raise ProcessingError("Prepared image exceeds size limit")
    return PreparedPage(number, "ocr_required", "", data, *binary.size)


def prepare_document(path: Path, media: str) -> list[PreparedPage]:
    if media in ("image/png", "image/jpeg"):
        with Image.open(path) as image:
            if image.width * image.height > 25_000_000:
                raise ProcessingError("Image dimensions exceed limit")
            return [prepare_image(image, 1)]
    if media != "application/pdf":
        raise ProcessingError("Unsupported document type")
    results = []
    with PDF_LOCK:
        with pdfium.PdfDocument(path) as pdf:
            if not 1 <= len(pdf) <= MAX_PAGES:
                raise ProcessingError("PDF must contain 1 to 20 pages")
            for index in range(len(pdf)):
                page = pdf[index]
                try:
                    text_page = page.get_textpage()
                    try:
                        if text_page.count_chars() > MAX_TEXT:
                            raise ProcessingError("Page text exceeds limit")
                        text = text_page.get_text_range().replace("\x00", "").strip()
                    finally:
                        text_page.close()
                    if text:
                        results.append(PreparedPage(index + 1, "embedded_text", text))
                    else:
                        width, height = page.get_size()
                        if min(width, height) <= 0:
                            raise ProcessingError("Invalid PDF page dimensions")
                        scale = min(200 / 72, MAX_SIDE / max(width, height))
                        bitmap = page.render(scale=scale)
                        try:
                            results.append(prepare_image(bitmap.to_pil(), index + 1))
                        finally:
                            bitmap.close()
                finally:
                    page.close()
    return results
