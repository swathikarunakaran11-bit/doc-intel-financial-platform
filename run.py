#!/usr/bin/env python3
"""
Launcher script for the Intelligent Financial Document Intelligence Platform.
Runs FastAPI backend with Jinja2 frontend and REST APIs.
"""
import sys
import os
from pathlib import Path

# Configure utf-8 encoding for standard output if supported
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root directory to Python path
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import uvicorn
from backend.app.core.config import settings
from backend.app.core.database import engine, Base
from backend.app.core.logging import logger

def main():
    # 1. Initialize SQLite / relational database schema
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "127.0.0.1")

    print("\n" + "=" * 70)
    print(" [DOC-INTEL] Intelligent Document Extraction & Financial Validation Platform")
    print("=" * 70)
    print(f" * Dashboard UI:      http://{host}:{port}/")
    print(f" * Swagger API Docs:  http://{host}:{port}/docs")
    print(f" * ReDoc API Docs:    http://{host}:{port}/redoc")
    print(f" * Health Check:      http://{host}:{port}/health")
    print(f" * Process API:       http://{host}:{port}{settings.API_V1_PREFIX}/documents/process")
    print("=" * 70 + "\n")

    uvicorn.run(
        "backend.app.main:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
