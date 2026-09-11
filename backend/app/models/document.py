import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, DateTime, JSON
from backend.app.core.database import Base

class DocumentRecord(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_name = Column(String(255), index=True, nullable=False)
    document_type = Column(String(50), index=True, nullable=False)
    file_type = Column(String(50), nullable=False)
    file_size = Column(Integer, nullable=False, default=0)
    page_count = Column(Integer, nullable=False, default=1)
    processing_status = Column(String(20), index=True, nullable=False, default="PASS")  # PASS | FAILED
    overall_confidence = Column(Float, nullable=True, default=1.0)
    
    # Complete JSON blobs
    file_validation = Column(JSON, nullable=False, default=dict)
    extracted_data = Column(JSON, nullable=False, default=dict)
    validation_results = Column(JSON, nullable=False, default=dict)
    processing_metadata = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "document_name": self.document_name,
            "document_type": self.document_type,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "page_count": self.page_count,
            "processing_status": self.processing_status,
            "overall_confidence": round(self.overall_confidence, 2) if self.overall_confidence is not None else None,
            "file_validation": self.file_validation,
            "extracted_data": self.extracted_data,
            "validation": self.validation_results,
            "processing_metadata": self.processing_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
