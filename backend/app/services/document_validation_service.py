import os
from io import BytesIO
from typing import Dict, Any, Tuple
from pypdf import PdfReader
from PIL import Image
from backend.app.core.config import settings
from backend.app.core.logging import logger

class DocumentValidationError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: Dict[str, Any] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}

class DocumentValidationService:
    @staticmethod
    def validate_file(
        filename: str,
        content: bytes,
        content_type: str = ""
    ) -> Dict[str, Any]:
        """
        Validates uploaded file against format, size, readability, and page limits.
        Raises DocumentValidationError on failure or returns the structured file_validation block.
        """
        logger.info(f"Validating file: {filename} (Size: {len(content)} bytes, Type: {content_type})")
        
        # 1. Check empty file
        if not content or len(content) == 0:
            raise DocumentValidationError(
                code="EMPTY_FILE",
                message="The uploaded file is empty (0 bytes).",
                status_code=400,
                details={"file_name": filename, "status": "FAILED"}
            )
            
        # 2. Check maximum file size
        if len(content) > settings.MAX_FILE_SIZE_BYTES:
            raise DocumentValidationError(
                code="FILE_TOO_LARGE",
                message=f"File exceeds maximum allowed size of {settings.MAX_FILE_SIZE_BYTES // (1024 * 1024)}MB.",
                status_code=400,
                details={"file_name": filename, "status": "FAILED"}
            )

        # 3. Detect extension and MIME
        ext = os.path.splitext(filename)[1].lower()
        
        detected_mime = "application/octet-stream"
        if ext in [".pdf"]:
            detected_mime = "application/pdf"
        elif ext in [".jpg", ".jpeg"]:
            detected_mime = "image/jpeg"
        elif ext in [".png"]:
            detected_mime = "image/png"
        else:
            # Check content-type header if ext isn't obvious
            if content_type in settings.ALLOWED_MIME_TYPES:
                detected_mime = content_type
            else:
                raise DocumentValidationError(
                    code="UNSUPPORTED_FILE_TYPE",
                    message="Only PDF / JPG / PNG documents are supported.",
                    status_code=400,
                    details={
                        "file_type": content_type or "unknown",
                        "is_supported": False,
                        "is_readable": False,
                        "page_count": 0,
                        "status": "FAILED"
                    }
                )

        if ext not in settings.ALLOWED_EXTENSIONS and detected_mime not in settings.ALLOWED_MIME_TYPES:
            raise DocumentValidationError(
                code="UNSUPPORTED_FILE_TYPE",
                message="Only PDF / JPG / PNG documents are supported.",
                status_code=400,
                details={
                    "file_type": detected_mime,
                    "is_supported": False,
                    "is_readable": False,
                    "page_count": 0,
                    "status": "FAILED"
                }
            )

        # 4. Readability and Page Count Validation
        page_count = 1
        is_readable = False

        if detected_mime == "application/pdf":
            try:
                reader = PdfReader(BytesIO(content))
                # Trigger a read check
                page_count = len(reader.pages)
                if page_count == 0:
                    raise ValueError("PDF has 0 pages.")
                # Verify first page can be read
                _ = reader.pages[0].extract_text()
                is_readable = True
            except Exception as e:
                logger.error(f"Failed to read PDF {filename}: {e}")
                raise DocumentValidationError(
                    code="CORRUPTED_FILE",
                    message=f"The uploaded PDF file is corrupted or cannot be read: {str(e)}",
                    status_code=400,
                    details={
                        "file_type": detected_mime,
                        "is_supported": True,
                        "is_readable": False,
                        "page_count": 0,
                        "status": "FAILED"
                    }
                )
        else:
            # Image validation
            try:
                img = Image.open(BytesIO(content))
                img.verify()  # Verify image integrity
                # Reopen to read frames/dimensions
                img = Image.open(BytesIO(content))
                page_count = getattr(img, "n_frames", 1)
                is_readable = True
            except Exception as e:
                logger.error(f"Failed to read image {filename}: {e}")
                raise DocumentValidationError(
                    code="CORRUPTED_FILE",
                    message=f"The uploaded image is corrupted or invalid: {str(e)}",
                    status_code=400,
                    details={
                        "file_type": detected_mime,
                        "is_supported": True,
                        "is_readable": False,
                        "page_count": 0,
                        "status": "FAILED"
                    }
                )

        # 5. Page Limit Check (<= 3 pages)
        if page_count > settings.MAX_PAGE_LIMIT:
            logger.warning(f"File {filename} exceeds page limit: {page_count} > {settings.MAX_PAGE_LIMIT}")
            raise DocumentValidationError(
                code="PAGE_LIMIT_EXCEEDED",
                message=f"Document exceeds maximum page limit of {settings.MAX_PAGE_LIMIT} pages. Uploaded document has {page_count} pages.",
                status_code=400,
                details={
                    "file_type": detected_mime,
                    "is_supported": True,
                    "is_readable": True,
                    "page_count": page_count,
                    "status": "FAILED"
                }
            )

        validation_result = {
            "file_type": detected_mime,
            "is_supported": True,
            "is_readable": is_readable,
            "page_count": page_count,
            "status": "PASS"
        }
        logger.info(f"File validation passed for {filename}: {validation_result}")
        return validation_result
