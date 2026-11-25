"""Local Tesseract adapter with bounded execution and structured word output."""
import csv
import subprocess
import tempfile
from io import BytesIO
from pathlib import Path

from PIL import Image
from pydantic import BaseModel, Field


class OCRWord(BaseModel):
    text: str
    confidence: float = Field(ge=0, le=100)
    left: int
    top: int
    width: int
    height: int


class OCRResult(BaseModel):
    text: str
    words: list[OCRWord]
    mean_confidence: float | None


class OCRError(RuntimeError):
    pass


def parse_words(data: dict) -> OCRResult:
    words = []
    lines = {}
    for i, raw in enumerate(data['text']):
        text = raw.strip().replace('\x00', '')
        confidence = float(data['conf'][i])
        if not text or not 0 <= confidence <= 100:
            continue
        word = OCRWord(text=text, confidence=confidence, **{
            key: int(data[key][i]) for key in ('left', 'top', 'width', 'height')
        })
        words.append(word)
        line = tuple(data[key][i] for key in ('block_num', 'par_num', 'line_num'))
        lines.setdefault(line, []).append(text)
    return OCRResult(
        text='\n'.join(' '.join(line) for line in lines.values()),
        words=words,
        mean_confidence=round(sum(w.confidence for w in words) / len(words), 2)
        if words else None,
    )


def recognize(image_png: bytes, executable: str, language: str, timeout: int) -> OCRResult:
    # Use a per-call subprocess with an explicit executable.
    try:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'page.png'
            with Image.open(BytesIO(image_png)) as image:
                image.save(path)
            result = subprocess.run(
                [executable, str(path), 'stdout', '-l', language, '--psm', '6', 'tsv'],
                capture_output=True, timeout=timeout, check=True,
            )
            reader = csv.DictReader(
                result.stdout.decode("utf-8").splitlines(),
                delimiter="\t", quoting=csv.QUOTE_NONE,
            )
            data = {key: [] for key in (reader.fieldnames or [])}
            for row in reader:
                for key in data:
                    data[key].append(row[key] or "")
            return parse_words(data)
    except (OSError, subprocess.SubprocessError, ValueError, KeyError, TypeError) as exc:
        raise OCRError('OCR failed; check Tesseract installation, language and timeout') from exc
