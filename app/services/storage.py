import hashlib
import warnings
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from PIL import Image
from pypdf import PdfReader

FORMATS = {".pdf": "application/pdf", ".png": "image/png",
           ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}


class InvalidDocument(ValueError):
    pass


class DocumentTooLarge(ValueError):
    pass


def store_document(source: BinaryIO, filename: str, root: Path, limit: int):
    name = filename.replace("\\", "/").split("/")[-1]
    if not name or len(name) > 255 or any(ord(c) < 32 for c in name):
        raise InvalidDocument("Invalid filename")
    suffix = Path(name).suffix.lower()
    if suffix not in FORMATS:
        raise InvalidDocument("Only PDF, PNG and JPEG are supported")
    root.mkdir(parents=True, exist_ok=True)
    key = uuid4().hex + suffix
    path = root / key
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("xb") as output:
            while chunk := source.read(65536):
                size += len(chunk)
                if size > limit:
                    raise DocumentTooLarge("File exceeds configured limit")
                digest.update(chunk)
                output.write(chunk)
        if not size:
            raise InvalidDocument("Empty document")
        try:
            if suffix == ".pdf":
                with path.open("rb") as stream:
                    if stream.read(5) != b"%PDF-":
                        raise ValueError("Invalid PDF signature")
                    stream.seek(0)
                    reader = PdfReader(stream, strict=True)
                    if reader.is_encrypted or not len(reader.pages):
                        raise ValueError("Encrypted or empty PDF")
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(path) as image:
                        expected = "PNG" if suffix == ".png" else "JPEG"
                        if image.format != expected or image.width * image.height > 25_000_000:
                            raise ValueError("Invalid image format or dimensions")
                        image.verify()
                    with Image.open(path) as image:
                        image.load()
        except Exception as exc:
            raise InvalidDocument("Invalid or unsupported document content") from exc
        return name, key, FORMATS[suffix], size, digest.hexdigest()
    except Exception:
        path.unlink(missing_ok=True)
        raise
