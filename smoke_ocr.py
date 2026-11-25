from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from app.core.config import Settings
from app.services.ocr import recognize

settings = Settings()
image = Image.new('RGB', (1000, 200), 'white')
ImageDraw.Draw(image).text((30, 30), 'Invoice 123', fill='black',
                          font=ImageFont.load_default(size=64))
buffer = BytesIO()
image.save(buffer, format='PNG')
result = recognize(buffer.getvalue(), settings.ocr_executable,
                   settings.ocr_language, settings.ocr_timeout)
print(result.model_dump_json(indent=2))
assert result.text == 'Invoice 123', 'Unexpected recognition result'
