from health.ocr_service import OCRService


ocr = OCRService()

text = ocr.extract_text(
    "dc.png"
)

print()

print("=" * 50)

print(text)

print("=" * 50)