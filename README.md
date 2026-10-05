# DocIntel — Financial Document Parser & Accounting Validator

A backend service built with **FastAPI**, **RapidOCR (ONNX)**, and **pypdfium2** to parse financial documents (Invoices, Balance Sheets, Cash Flows) and check basic accounting math rules.

Runs directly on CPU without needing system installs like Tesseract or Poppler.

---

## Quickstart

### 1. Run with Docker
```bash
git clone https://github.com/swathikarunakaran11-bit/doc-intel-financial-platform.git
cd doc-intel-financial-platform
docker-compose up --build
