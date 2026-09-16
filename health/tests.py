from health.ai.extractor_service import PrescriptionExtractor

document_text = """
Tab Metformin 500 mg

Morning

Night

After Food

90 Days

Tab Dolo 650

SOS
"""

extractor = PrescriptionExtractor()
result = extractor.extract(document_text)
print(result)
