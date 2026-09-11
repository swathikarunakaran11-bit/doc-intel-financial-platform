from typing import Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.services.document_service import DocumentService
from backend.app.services.document_validation_service import DocumentValidationError
from backend.app.schemas.document import (
    ProcessedDocumentResponse,
    DocumentListResponse,
    ErrorResponse
)

router = APIRouter()

# -----------------------------------------------------------------------------
# Health Check Endpoint
# -----------------------------------------------------------------------------
@router.get(
    "/health",
    summary="Service Health Check",
    description="Returns operational status of the service, database connectivity and version information."
)
def health_check(db: Session = Depends(get_db)):
    # Check DB connection
    db_healthy = True
    try:
        from sqlalchemy import text
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_healthy = False

    return {
        "status": "healthy" if db_healthy else "degraded",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": settings.VERSION,
        "database": "connected" if db_healthy else "disconnected",
        "environment": settings.ENVIRONMENT
    }

# -----------------------------------------------------------------------------
# Document Upload & Processing Endpoint
# -----------------------------------------------------------------------------
@router.post(
    "/documents/process",
    response_model=ProcessedDocumentResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Validation or file format failure"},
        500: {"model": ErrorResponse, "description": "Internal processing error"}
    },
    summary="Upload & Process Financial Document",
    description="Accepts a PDF, JPG, or PNG financial document (max 3 pages), extracts all visible fields/tables, validates financial relationships, persists result, and returns structured JSON."
)
async def process_document(
    file: UploadFile = File(..., description="Document file in PDF, JPG, or PNG format (max 3 pages)"),
    document_type: str = Form(..., description="Type of document: invoice | balance_sheet | profit_and_loss | cash_flow_statement"),
    db: Session = Depends(get_db)
):
    # Validate document_type
    valid_types = ["invoice", "balance_sheet", "profit_and_loss", "cash_flow_statement", "pnl", "cash_flow"]
    norm_doc_type = document_type.lower().strip().replace("-", "_").replace(" ", "_")
    if norm_doc_type not in valid_types:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_DOCUMENT_TYPE",
                    "message": f"Unsupported document type '{document_type}'. Supported types: invoice, balance_sheet, profit_and_loss, cash_flow_statement."
                }
            }
        )

    try:
        content = await file.read()
        service = DocumentService(db)
        result = service.process_document(
            filename=file.filename or "uploaded_document",
            content=content,
            document_type=norm_doc_type,
            content_type=file.content_type or ""
        )
        return result
    except DocumentValidationError as ve:
        logger.warning(f"File validation error on '{file.filename}': {ve.code} - {ve.message}")
        return JSONResponse(
            status_code=ve.status_code,
            content={
                "error": {
                    "code": ve.code,
                    "message": ve.message
                }
            }
        )
    except Exception as e:
        logger.error(f"Unexpected processing exception on '{file.filename}': {e}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "PROCESSING_ERROR",
                    "message": "An error occurred while processing the document. Please verify the document format."
                }
            }
        )

# -----------------------------------------------------------------------------
# Retrieve Latest Structured Result by Document Name
# -----------------------------------------------------------------------------
@router.get(
    "/documents/{document_name:path}",
    response_model=ProcessedDocumentResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Document not found"}
    },
    summary="Retrieve Latest Processed Result by File Name",
    description="Fetches the most recently processed structured JSON output for a given document name."
)
def get_document_by_name(document_name: str, db: Session = Depends(get_db)):
    service = DocumentService(db)
    result = service.get_latest_by_name(document_name)
    if not result:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={
                "error": {
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": f"No processed record found for document name '{document_name}'."
                }
            }
        )
    return result

# -----------------------------------------------------------------------------
# List Processed Documents (for Dashboard)
# -----------------------------------------------------------------------------
@router.get(
    "/documents",
    response_model=DocumentListResponse,
    summary="List Processed Documents",
    description="Retrieves a list of processed documents with status, confidence, and metadata for dashboard display."
)
def list_documents(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    document_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    query: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    service = DocumentService(db)
    return service.list_documents(
        skip=skip,
        limit=limit,
        doc_type=document_type,
        status=status,
        query=query
    )
