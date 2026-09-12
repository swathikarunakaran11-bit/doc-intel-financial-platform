import sys, os
sys.path.insert(0, os.path.abspath("."))
from backend.app.services.ocr_service import OCRService
from backend.app.services.extraction_service import ExtractionService
import json

with open('dataset/Dataset/Invoices/batch2-0499.jpg', 'rb') as f:
    content = f.read()

pages = OCRService.extract_text_with_pages(content, 'image/jpeg', 'batch2-0499.jpg')
lines_with_page = []
for p in pages:
    for l in p.get("lines", []):
        lines_with_page.append((l, p["page_number"]))

data, conf = ExtractionService.extract_document_data("invoice", pages)
print("\n--- EXTRACTED FIELDS ---")
for k, v in data.items():
    if isinstance(v, dict) and 'value' in v:
        val = v.get('value')
        conf = v.get('confidence')
        ev = v.get('evidence')
        print(f"{k}: {val} (conf: {conf}) -> evidence: {ev}")

from backend.app.services.financial_validation_service import FinancialValidationService
validator = FinancialValidationService()
val_result = validator.validate("invoice", data)
print("\n--- VALIDATION CHECKS ---")
for c in val_result['checks']:
    print(f"{c['name']}: status={c['status']}, formula={c['formula']}, calc={c['calculated_value']}, rep={c['reported_value']}, var={c['variance']}")
print("Overall status:", val_result['overall_status'])
