#!/usr/bin/env python3
"""
Seeds documents from dataset/Dataset into the platform database.
"""
import sys
import os
from pathlib import Path

# Force utf-8 output if supported
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.services.document_service import DocumentService
from backend.app.core.logging import logger

def seed_dataset(limit_per_category: int = 3):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    service = DocumentService(db)

    dataset_root = ROOT_DIR / "dataset" / "Dataset"
    if not dataset_root.exists():
        print(f"Dataset root not found at {dataset_root}")
        return

    categories = [
        ("Balance Sheet", "balance_sheet", "application/pdf"),
        ("Profit & Loss", "profit_and_loss", "application/pdf"),
        ("Cash Flows", "cash_flow_statement", "application/pdf"),
        ("Invoices", "invoice", "image/jpeg")
    ]

    total_processed = 0

    print("=" * 60)
    print(" Ingesting and Validating Sample Dataset Documents")
    print("=" * 60)

    for folder_name, doc_type, mime_type in categories:
        folder = dataset_root / folder_name
        if not folder.exists():
            continue

        files = [f for f in folder.iterdir() if f.is_file()]
        selected_files = files[:limit_per_category] if limit_per_category > 0 else files

        print(f"\nProcessing {len(selected_files)} documents from [{folder_name}]:")

        for file_path in selected_files:
            try:
                with open(file_path, "rb") as f:
                    content = f.read()

                res = service.process_document(
                    filename=file_path.name,
                    content=content,
                    document_type=doc_type,
                    content_type=mime_type
                )
                status = res["processing_status"]
                val_status = res["validation"]["overall_status"]
                checks = len(res["validation"]["checks"])
                conf = int((res["overall_confidence"] or 0) * 100)
                print(f"  [OK] {file_path.name:<38} | Status: {status} | Math Checks: {checks} ({val_status}) | Conf: {conf}%")
                total_processed += 1
            except Exception as e:
                print(f"  [ERROR] {file_path.name:<38} | Error: {e}")

    db.close()
    print(f"\nSeeding complete! Ingested {total_processed} documents into database.")

if __name__ == "__main__":
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    seed_dataset(limit_per_category=limit)
