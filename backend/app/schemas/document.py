from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class FileValidationBlock(BaseModel):
    file_type: str
    is_supported: bool
    is_readable: bool
    page_count: int
    status: str  # PASS | FAILED
    error_message: Optional[str] = None

class ValidationCheckItem(BaseModel):
    name: str
    formula: str
    operands: Dict[str, Any] = Field(default_factory=dict)
    calculated_value: Optional[float] = None
    reported_value: Optional[float] = None
    variance: Optional[float] = None
    status: str  # PASS | FAIL | NOT_APPLICABLE
    description: Optional[str] = None

class ValidationBlock(BaseModel):
    checks: List[ValidationCheckItem] = Field(default_factory=list)
    overall_status: str = "PASS"  # PASS | FAIL
    issues: List[str] = Field(default_factory=list)

class ProcessingMetadataBlock(BaseModel):
    ocr_used: bool = False
    processed_at: str
    processing_time_ms: int
    extractor: str = "hybrid_intelligent_parser"

class ProcessedDocumentResponse(BaseModel):
    document_name: str
    document_type: str
    processing_status: str  # PASS | FAILED
    overall_confidence: Optional[float] = None
    file_validation: FileValidationBlock
    extracted_data: Dict[str, Any] = Field(default_factory=dict)
    validation: ValidationBlock
    processing_metadata: ProcessingMetadataBlock

class DocumentListItem(BaseModel):
    id: str
    document_name: str
    document_type: str
    file_type: str
    page_count: int
    processing_status: str
    overall_confidence: Optional[float]
    created_at: Optional[str]
    processing_time_ms: Optional[int] = None

class DocumentListResponse(BaseModel):
    total: int
    items: List[DocumentListItem]

class ErrorDetail(BaseModel):
    code: str
    message: str

class ErrorResponse(BaseModel):
    error: ErrorDetail
