from typing import List, Optional, Tuple
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.models.document import DocumentRecord

class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_or_update(
        self,
        document_name: str,
        document_type: str,
        file_type: str,
        file_size: int,
        page_count: int,
        processing_status: str,
        overall_confidence: Optional[float],
        file_validation: dict,
        extracted_data: dict,
        validation_results: dict,
        processing_metadata: dict,
    ) -> DocumentRecord:
        # Check if a document with this name already exists
        existing = (
            self.db.query(DocumentRecord)
            .filter(DocumentRecord.document_name == document_name)
            .order_by(desc(DocumentRecord.created_at))
            .first()
        )

        if existing:
            # Update existing latest record
            existing.document_type = document_type
            existing.file_type = file_type
            existing.file_size = file_size
            existing.page_count = page_count
            existing.processing_status = processing_status
            existing.overall_confidence = overall_confidence
            existing.file_validation = file_validation
            existing.extracted_data = extracted_data
            existing.validation_results = validation_results
            existing.processing_metadata = processing_metadata
            existing.updated_at = datetime.now(timezone.utc)
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            record = DocumentRecord(
                document_name=document_name,
                document_type=document_type,
                file_type=file_type,
                file_size=file_size,
                page_count=page_count,
                processing_status=processing_status,
                overall_confidence=overall_confidence,
                file_validation=file_validation,
                extracted_data=extracted_data,
                validation_results=validation_results,
                processing_metadata=processing_metadata,
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record

    def get_by_name(self, document_name: str) -> Optional[DocumentRecord]:
        return (
            self.db.query(DocumentRecord)
            .filter(DocumentRecord.document_name == document_name)
            .order_by(desc(DocumentRecord.created_at))
            .first()
        )

    def get_by_id(self, doc_id: str) -> Optional[DocumentRecord]:
        return self.db.query(DocumentRecord).filter(DocumentRecord.id == doc_id).first()

    def list_all(
        self,
        skip: int = 0,
        limit: int = 50,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        query: Optional[str] = None
    ) -> Tuple[List[DocumentRecord], int]:
        q = self.db.query(DocumentRecord)
        if doc_type:
            q = q.filter(DocumentRecord.document_type == doc_type)
        if status:
            q = q.filter(DocumentRecord.processing_status == status)
        if query:
            q = q.filter(DocumentRecord.document_name.ilike(f"%{query}%"))
            
        total = q.count()
        items = q.order_by(desc(DocumentRecord.created_at)).offset(skip).limit(limit).all()
        return items, total

    def delete_by_id(self, doc_id: str) -> bool:
        rec = self.get_by_id(doc_id)
        if rec:
            self.db.delete(rec)
            self.db.commit()
            return True
        return False
