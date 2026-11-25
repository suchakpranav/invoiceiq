from pathlib import Path

from PIL import Image, ImageDraw

directory = Path("sample_data")
directory.mkdir(exist_ok=True)

image = Image.new("RGB", (1240, 1754), "white")
draw = ImageDraw.Draw(image)

lines = [
    "SAMPLE TAX INVOICE",
    "",
    "Invoice No: INV-DEMO-001",
    "Supplier: Sample Traders",
    "Customer: Demo Retail",
    "Date: 26-11-2026",
    "",
    "Product: Office Equipment",
    "Quantity: 5",
    "Subtotal: INR 25000.00",
    "GST (18%): INR 4500.00",
    "Total: INR 29500.00",
    "",
    "Synthetic document for testing only."
]

y = 80

for line in lines:
    draw.text(
        (80, y),
        line,
        fill="black",
        font_size=32
    )
    y += 65

image.save(directory / "sample_invoice.png")

image.save(
    directory / "sample_invoice.jpg",
    quality=95
)

image.save(
    directory / "sample_invoice.pdf",
    "PDF",
    resolution=150.0
)

print("Sample documents generated successfully.")