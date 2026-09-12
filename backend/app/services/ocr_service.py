import os
from io import BytesIO
from typing import List, Dict, Any, Optional
from pypdf import PdfReader
from PIL import Image
from backend.app.core.logging import logger

class OCRService:
    @staticmethod
    def extract_text_with_pages(
        content: bytes,
        mime_type: str,
        filename: str = ""
    ) -> List[Dict[str, Any]]:
        """
        Extracts text from PDF or images, segmenting by page number.
        Returns a list of dicts: [{'page_number': 1, 'text': '...', 'lines': [...]}]
        """
        pages_data = []

        if mime_type == "application/pdf":
            try:
                reader = PdfReader(BytesIO(content))
                for idx, page in enumerate(reader.pages):
                    page_num = idx + 1
                    raw_text = page.extract_text() or ""
                    # Normalize lines
                    lines = [line.strip() for line in raw_text.splitlines() if line.strip()]
                    pages_data.append({
                        "page_number": page_num,
                        "text": raw_text.strip(),
                        "lines": lines,
                        "ocr_applied": False
                    })
                logger.info(f"Extracted native text from {len(pages_data)} PDF pages of {filename}")
            except Exception as e:
                logger.warning(f"Native PDF extraction warning for {filename}: {e}")

        # If pages_data is empty or all pages have empty/minimal text (vector-curved or scanned PDF)
        has_sufficient_text = any(len(p.get("text", "").strip()) > 40 for p in pages_data) if pages_data else False

        if mime_type == "application/pdf" and not has_sufficient_text:
            logger.info(f"Applying PDF page rendering and OCR extraction for {filename}")
            pdf_ocr_pages = OCRService._run_pdf_ocr(content, filename)
            if pdf_ocr_pages and any(p.get("text") for p in pdf_ocr_pages):
                pages_data = pdf_ocr_pages

        elif mime_type.startswith("image/"):
            logger.info(f"Applying image-based OCR / text extraction for {filename}")
            ocr_pages = OCRService._run_image_ocr(content, mime_type)
            if ocr_pages:
                pages_data = ocr_pages

        # Ensure at least one page record
        if not pages_data:
            pages_data = [{
                "page_number": 1,
                "text": "",
                "lines": [],
                "ocr_applied": True
            }]

        return pages_data

    @staticmethod
    def _run_pdf_ocr(content: bytes, filename: str = "") -> List[Dict[str, Any]]:
        """
        Renders PDF pages into images using pypdfium2 and extracts text via RapidOCR.
        Handles scanned PDFs and vector-outlined text (such as financial annual reports).
        """
        results = []
        try:
            import pypdfium2 as pdfium
            import numpy as np
            from rapidocr_onnxruntime import RapidOCR

            pdf = pdfium.PdfDocument(content)
            engine = RapidOCR()
            num_pages = len(pdf)

            for idx in range(min(num_pages, 5)):  # Process up to 5 pages per pre-flight limit
                page = pdf[idx]
                image = page.render(scale=1.0).to_pil()
                if image.width > 1200 or image.height > 1200:
                    image.thumbnail((1200, 1200))
                img_np = np.array(image)
                ocr_res, _ = engine(img_np)

                lines = []
                if ocr_res:
                    lines = [str(item[1]).strip() for item in ocr_res if item and len(item) > 1 and item[1]]
                
                results.append({
                    "page_number": idx + 1,
                    "text": "\n".join(lines),
                    "lines": lines,
                    "ocr_applied": True
                })

            total_lines = sum(len(r["lines"]) for r in results)
            logger.info(f"RapidOCR PDF extraction succeeded for {filename}: {total_lines} lines across {len(results)} pages.")
            return results
        except Exception as err:
            logger.warning(f"RapidOCR PDF extraction fallback/failed for {filename}: {err}")
            return []

    @staticmethod
    def _run_image_ocr(content: bytes, mime_type: str) -> List[Dict[str, Any]]:
        """
        Runs RapidOCR (ONNX Runtime) or falls back to Tesseract.
        """
        results = []

        # 1. Try RapidOCR (high performance, self-contained ONNX engine)
        try:
            from rapidocr_onnxruntime import RapidOCR
            import numpy as np
            engine = RapidOCR()
            try:
                pil_img = Image.open(BytesIO(content)).convert("RGB")
                if pil_img.width > 1200 or pil_img.height > 1200:
                    pil_img.thumbnail((1200, 1200))
                img_np = np.array(pil_img)
                ocr_res, _ = engine(img_np)
            except Exception:
                ocr_res, _ = engine(content)

            if ocr_res:
                lines = [str(item[1]).strip() for item in ocr_res if item and len(item) > 1 and item[1]]
                full_text = "\n".join(lines)
                results.append({
                    "page_number": 1,
                    "text": full_text,
                    "lines": lines,
                    "ocr_applied": True
                })
                logger.info(f"Successfully executed RapidOCR: extracted {len(lines)} lines.")
                return results
        except Exception as r_err:
            logger.info(f"RapidOCR fallback or failed: {r_err}")

        # 2. Try Pytesseract
        try:
            import pytesseract
            img = Image.open(BytesIO(content))
            text = pytesseract.image_to_string(img)
            lines = [l.strip() for l in text.splitlines() if l.strip()]
            results.append({
                "page_number": 1,
                "text": text.strip(),
                "lines": lines,
                "ocr_applied": True
            })
            logger.info("Successfully executed local Tesseract OCR.")
            return results
        except Exception as t_err:
            logger.info(f"Pytesseract not available or failed ({t_err}).")

        # 3. Fallback: Image without external OCR binary
        results.append({
            "page_number": 1,
            "text": "",
            "lines": [],
            "ocr_applied": True
        })
        return results
