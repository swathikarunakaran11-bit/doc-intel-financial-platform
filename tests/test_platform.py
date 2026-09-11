import io
import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.services.financial_validation_service import FinancialValidationService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "version" in data
    assert "database" in data

def test_dashboard_html_view():
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "DocIntel AI" in response.text
    assert "Ingest Financial Document" in response.text

def test_list_documents_api():
    response = client.get("/api/v1/documents")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)

def test_document_detail_view():
    # Fetch existing docs to get a valid name
    list_res = client.get("/api/v1/documents")
    items = list_res.json().get("items", [])
    if items:
        test_doc_name = items[0]["document_name"]
        response = client.get(f"/view/{test_doc_name}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert test_doc_name in response.text

def test_get_document_by_name_api():
    list_res = client.get("/api/v1/documents")
    items = list_res.json().get("items", [])
    if items:
        test_doc_name = items[0]["document_name"]
        response = client.get(f"/api/v1/documents/{test_doc_name}")
        assert response.status_code == 200
        data = response.json()
        assert data["document_name"] == test_doc_name
        assert "extracted_data" in data
        assert "validation" in data

def test_financial_validation_balance_sheet():
    validator = FinancialValidationService(tolerance=0.05)
    extracted_data = {
        "periods": ["FY2024"],
        "total_assets": {"FY2024": {"value": 150000.0, "confidence": 0.95}},
        "total_liabilities": {"FY2024": {"value": 90000.0, "confidence": 0.95}},
        "total_equity": {"FY2024": {"value": 60000.0, "confidence": 0.95}},
    }
    result = validator.validate("balance_sheet", extracted_data)
    assert result["overall_status"] == "PASS"
    assert len(result["checks"]) >= 1
    check = result["checks"][0]
    assert check["status"] == "PASS"
    assert check["variance"] == 0.0

def test_financial_validation_invoice_line_items():
    validator = FinancialValidationService(tolerance=0.05)
    extracted_data = {
        "subtotal": 100.0,
        "tax_amount": 10.0,
        "discount": 5.0,
        "total_amount": 105.0,
        "line_items": [
            {"description": "Item A", "quantity": 2, "unit_price": 25.0, "amount": 50.0},
            {"description": "Item B", "quantity": 5, "unit_price": 10.0, "amount": 50.0}
        ]
    }
    result = validator.validate("invoice", extracted_data)
    assert result["overall_status"] == "PASS"
    checks = {c["name"]: c for c in result["checks"]}
    assert "invoice_total_check" in checks
    assert checks["invoice_total_check"]["status"] == "PASS"
    assert checks["invoice_total_check"]["variance"] == 0.0

def test_invalid_document_type_rejected():
    fake_file = io.BytesIO(b"%PDF-1.4 test content")
    response = client.post(
        "/api/v1/documents/process",
        files={"file": ("test.pdf", fake_file, "application/pdf")},
        data={"document_type": "unknown_type"}
    )
    assert response.status_code == 400
    err = response.json()
    assert "INVALID_DOCUMENT_TYPE" in err["error"]["code"]

def test_balance_sheet_validation_equality():
    validator = FinancialValidationService(tolerance=0.05)
    extracted_data = {
        "periods": ["FY2025", "FY2024"],
        "total_assets": {
            "FY2025": {"value": 4392417.42},
            "FY2024": {"value": 4030194.26}
        },
        "total_capital_and_liabilities": {
            "FY2025": {"value": 4392417.42},
            "FY2024": {"value": 4030194.26}
        }
    }
    result = validator.validate("balance_sheet", extracted_data)
    assert result["overall_status"] == "PASS"
    checks = {c["name"]: c for c in result["checks"]}
    assert "balance_sheet_equality_check_FY2025" in checks
    assert checks["balance_sheet_equality_check_FY2025"]["status"] == "PASS"
    assert checks["balance_sheet_equality_check_FY2025"]["variance"] == 0.0
    assert checks["balance_sheet_equality_check_FY2024"]["status"] == "PASS"

def test_balance_sheet_pdf_ocr_extraction():
    import os
    from backend.app.services.ocr_service import OCRService
    from backend.app.services.extraction_service import ExtractionService
    
    pdf_path = "dataset/Dataset/Balance Sheet/Consolidated Balance Sheet 2025.pdf"
    if os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            content = f.read()
        pages = OCRService.extract_text_with_pages(content, "application/pdf", "Consolidated Balance Sheet 2025.pdf")
        assert len(pages) >= 1
        data, conf = ExtractionService.extract_document_data("balance_sheet", pages)
        assert "FY2025" in data["periods"]
        assert data["total_assets"]["FY2025"]["value"] == 4392417.42
        assert data["total_capital_and_liabilities"]["FY2025"]["value"] == 4392417.42
        assert data["entity_name"]["value"] == "HDFC Bank Limited"

