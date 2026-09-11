import os
from pathlib import Path
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.database import engine, Base, get_db
from backend.app.core.logging import logger
from backend.app.api.routes import documents
from backend.app.services.document_service import DocumentService
from backend.app.services.document_validation_service import DocumentValidationError

# Initialize Database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="End-to-End AI-powered document extraction and financial calculation validation platform for Invoices, Balance Sheets, Profit & Loss Statements, and Cash Flow Statements.",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "frontend" / "templates"
STATIC_DIR = BASE_DIR / "frontend" / "static"

# Ensure directories exist
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

# Mount Static Files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API Router
app.include_router(documents.router, prefix=settings.API_V1_PREFIX, tags=["Documents"])

# Root Health alias
@app.get("/health", include_in_schema=False)
def root_health_check(db: Session = Depends(get_db)):
    return documents.health_check(db)

# -----------------------------------------------------------------------------
# Frontend Web Routes
# -----------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def dashboard_view(request: Request, db: Session = Depends(get_db)):
    """Serves the main interactive dashboard."""
    service = DocumentService(db)
    docs_data = service.list_documents(limit=100)
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "documents": docs_data["items"],
            "total": docs_data["total"],
            "version": settings.VERSION
        }
    )

@app.get("/view/{document_name:path}", response_class=HTMLResponse, include_in_schema=False)
def document_detail_view(request: Request, document_name: str, db: Session = Depends(get_db)):
    """Serves the detailed document result inspector view."""
    service = DocumentService(db)
    doc_data = service.get_latest_by_name(document_name)
    if not doc_data:
        raise HTTPException(status_code=404, detail="Document not found")
    
    return templates.TemplateResponse(
        request=request,
        name="document_result.html",
        context={
            "doc": doc_data,
            "document_name": document_name,
            "version": settings.VERSION
        }
    )

@app.get("/raw-file/{document_name:path}", include_in_schema=False)
def serve_raw_file(document_name: str):
    """Serves the original document (PDF or image) for the split-screen document preview."""
    # 1. Check storage/uploads
    up_path = BASE_DIR / "storage" / "uploads" / document_name
    if up_path.exists():
        media_type = "application/pdf" if document_name.lower().endswith(".pdf") else "image/jpeg"
        return FileResponse(str(up_path), media_type=media_type)

    # 2. Check dataset
    for root, _, files in os.walk(BASE_DIR / "dataset"):
        if document_name in files:
            found_path = os.path.join(root, document_name)
            media_type = "application/pdf" if document_name.lower().endswith(".pdf") else "image/jpeg"
            return FileResponse(found_path, media_type=media_type)

    raise HTTPException(status_code=404, detail="Source document file not found")


# -----------------------------------------------------------------------------
# Global Exception Handlers
# -----------------------------------------------------------------------------
@app.exception_handler(DocumentValidationError)
async def validation_exception_handler(request: Request, exc: DocumentValidationError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": exc.code, "message": exc.message}}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": {"code": "HTTP_ERROR", "message": str(exc.detail)}}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
