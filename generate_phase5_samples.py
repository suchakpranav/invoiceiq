"""Generate synthetic fixtures, never real invoice data."""

from pathlib import Path

from PIL import Image, ImageDraw

from tests.test_processing import digital_pdf


def main():
    root = Path('sample_data')
    root.mkdir(exist_ok=True)
    digital_pdf(root / 'phase5_digital.pdf')
    image = Image.new('RGB', (1200, 1600), 'white')
    draw = ImageDraw.Draw(image)
    draw.text((80, 80), 'SYNTHETIC INVOICE\nINV-005\nTotal: INR 1180.00',
              fill='black', font_size=48)
    image.save(root / 'phase5_image.png')
    image.save(root / 'phase5_scanned.pdf', resolution=150)


if __name__ == '__main__':
    main()
