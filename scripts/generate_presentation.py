import os
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

def create_presentation(output_path="DocIntel_Development_Approach.pptx"):
    prs = Presentation()
    # 16:9 widescreen
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_slide_layout = prs.slide_layouts[6]

    # Theme colors (Dark Navy / Tech Blue / Emerald Accent)
    COLOR_BG = RGBColor(15, 23, 42)          # Slate 900
    COLOR_CARD = RGBColor(30, 41, 59)        # Slate 800
    COLOR_BORDER = RGBColor(51, 65, 85)      # Slate 700
    COLOR_PRIMARY = RGBColor(56, 189, 248)    # Sky 400
    COLOR_ACCENT = RGBColor(52, 211, 153)     # Emerald 400
    COLOR_TEXT_MAIN = RGBColor(248, 250, 252) # White
    COLOR_TEXT_MUTED = RGBColor(148, 163, 184)# Slate 400
    COLOR_HIGHLIGHT = RGBColor(251, 191, 36) # Amber 400

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, category, title):
        tb = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(1.2))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0
        
        p_cat = tf.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_PRIMARY
        p_cat.space_after = Pt(4)

        p_title = tf.add_paragraph()
        p_title.text = title
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_TEXT_MAIN

    def add_card(slide, left, top, width, height, title, points, accent_color=COLOR_PRIMARY):
        # Card background
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = COLOR_CARD
        card.line.color.rgb = COLOR_BORDER
        card.line.width = Pt(1.5)

        # Card content
        tb = slide.shapes.add_textbox(left + Inches(0.3), top + Inches(0.25), width - Inches(0.6), height - Inches(0.5))
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

        p_head = tf.paragraphs[0]
        p_head.text = title
        p_head.font.size = Pt(16)
        p_head.font.bold = True
        p_head.font.color.rgb = accent_color
        p_head.space_after = Pt(12)

        for pt_text in points:
            p = tf.add_paragraph()
            p.text = f"• {pt_text}"
            p.font.size = Pt(12.5)
            p.font.color.rgb = COLOR_TEXT_MAIN
            p.space_after = Pt(8)

    # -------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s1)

    tb1 = s1.shapes.add_textbox(Inches(1.0), Inches(1.8), Inches(11.3), Inches(3.8))
    tf1 = tb1.text_frame
    tf1.word_wrap = True

    p0 = tf1.paragraphs[0]
    p0.text = "FINANCIAL DOCUMENT INTELLIGENCE PLATFORM"
    p0.font.size = Pt(14)
    p0.font.bold = True
    p0.font.color.rgb = COLOR_PRIMARY
    p0.space_after = Pt(10)

    p1 = tf1.add_paragraph()
    p1.text = "Technical Development Approach & Architecture"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = COLOR_TEXT_MAIN
    p1.space_after = Pt(16)

    p2 = tf1.add_paragraph()
    p2.text = "An enterprise-grade platform engineered for automated OCR extraction, grounded provenance citations, and deterministic mathematical validation of Invoices, Balance Sheets, P&L, and Cash Flow Statements."
    p2.font.size = Pt(16)
    p2.font.color.rgb = COLOR_TEXT_MUTED
    p2.space_after = Pt(28)

    p3 = tf1.add_paragraph()
    p3.text = "Author: Swathi Karunakaran  |  Platform: FastAPI, ONNX Runtime, Jinja2, Docker, SQLite"
    p3.font.size = Pt(13)
    p3.font.bold = True
    p3.font.color.rgb = COLOR_ACCENT

    # -------------------------------------------------------------
    # SLIDE 2: Problem Statement & Objectives
    # -------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s2)
    add_header(s2, "Context & Challenges", "The Problem: Why Traditional Document Extraction Fails")

    add_card(s2, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "1. Brittle Rule-Based Systems",
             [
                 "Traditional regex and fixed-coordinate parsers break whenever layouts or font sizes vary.",
                 "Cannot handle noisy scans, skewed receipts, or multi-column financial tables.",
                 "High maintenance overhead for every new document template."
             ], COLOR_HIGHLIGHT)

    add_card(s2, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "2. Flawed Blind LLM Prompting",
             [
                 "Prone to financial hallucinations and inaccurate numbers.",
                 "Severe floating-point calculation errors in financial totals.",
                 "Massive token latency (5-15s), high cloud bills, and privacy concerns uploading sensitive records."
             ], COLOR_HIGHLIGHT)

    add_card(s2, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "3. Our Engineering Objectives",
             [
                 "Zero-dependency deployment: No complex binary dependencies like Tesseract or Poppler.",
                 "Deterministic Math Audit: Enforce accounting equations (Assets = Liabilities + Equity).",
                 "Grounded Provenance: Every single field links directly to source document citations."
             ], COLOR_ACCENT)

    # -------------------------------------------------------------
    # SLIDE 3: System Architecture
    # -------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s3)
    add_header(s3, "System Design", "High-Level Three-Tier Platform Architecture")

    add_card(s3, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "Tier 1: Ingestion & Hybrid OCR",
             [
                 "File validation via magic bytes check and format gating (PDF, PNG, JPG).",
                 "Pure Python rasterization and text extraction using pypdfium2.",
                 "Embedded ONNX Runtime RapidOCR model for scanned documents with sub-second execution.",
                 "Cross-platform: Runs anywhere without OS-level C++ binaries."
             ], COLOR_PRIMARY)

    add_card(s3, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "Tier 2: Structured Extraction & Audit",
             [
                 "Geometry-aware token clustering for financial tables and headers.",
                 "Extracts Invoices, Balance Sheets, P&L Statements, and Cash Flow Statements.",
                 "Deterministic accounting engine verifies strict invariants (tolerance: ±0.05).",
                 "Audit provenance: Captures page number and source context for each entity."
             ], COLOR_PRIMARY)

    add_card(s3, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "Tier 3: Presentation & Delivery",
             [
                 "Dual-Pane Interactive Web Inspector (FastAPI + Jinja2 + Modern CSS).",
                 "Left Pane: High-fidelity embedded document viewer.",
                 "Right Pane: Extracted entities, audit cards, and discrepancy badges.",
                 "FastAPI REST API with full OpenAPI documentation (/docs) for microservice integration."
             ], COLOR_ACCENT)

    # -------------------------------------------------------------
    # SLIDE 4: Deterministic Accounting Engine
    # -------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s4)
    add_header(s4, "Core Innovation", "Deterministic Financial Validation & Accounting Invariants")

    add_card(s4, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), 
             "Accounting Invariant Equations Enforced",
             [
                 "Balance Sheets: Total Assets == Total Liabilities + Total Equity",
                 "Balance Sheets: Total Assets == Total Capital & Liabilities",
                 "Invoices: Line Item Multiplication (Qty × Unit Price == Line Total)",
                 "Invoices: Invoice Total == Subtotal + Tax - Discounts",
                 "Profit & Loss: Gross Profit == Revenue - Cost of Goods Sold (COGS)",
                 "Profit & Loss: Net Profit == Operating Profit - Tax - Expenses",
                 "Cash Flow: Net Change == Operating CF + Investing CF + Financing CF",
                 "Configurable floating-point delta tolerance (default: ±0.05)."
             ], COLOR_PRIMARY)

    add_card(s4, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), 
             "Discrepancy Detection & Audit Mode",
             [
                 "Instant Discrepancy Flagging: If an invoice states $5,000 but line items sum to $4,800, the system flags the exact variance.",
                 "Fraud & Error Prevention: Catches forged documents, rounded arithmetic errors, and transposition mistakes.",
                 "Confidence Scoring: Combines OCR character confidence with mathematical consistency.",
                 "Human-in-the-Loop Routing: Documents failing invariants are routed to review queues with audit rationale."
             ], COLOR_ACCENT)

    # -------------------------------------------------------------
    # SLIDE 5: Evidence Grounding & Dual-Pane UX
    # -------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s5)
    add_header(s5, "User Experience & Transparency", "Grounded Provenance Citations & Dual-Pane UI")

    add_card(s5, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), 
             "Full Audit Provenance & Grounding",
             [
                 "Zero Blind Extraction: Every extracted figure includes an evidence citation object.",
                 "Source Metadata: Captures exact page number and surrounding bounding text quote.",
                 "Compliance & Regulatory Ready: Provides financial auditors with an immutable audit trail for SOX/IFRS compliance.",
                 "Reviewers verify numbers in 5 seconds instead of reading 30-page annual reports."
             ], COLOR_PRIMARY)

    add_card(s5, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), 
             "Enterprise Dual-Pane Split-Screen UI",
             [
                 "Side-by-Side Verification: Original PDF previewed synchronously alongside structured data.",
                 "Visual Audit Cards: Displays green verification badges for passed equations and red alerts for discrepancies.",
                 "Document History & Search: Filter and inspect past processed documents stored in SQLite.",
                 "Export Capabilities: Download processed records as validated structured JSON."
             ], COLOR_ACCENT)

    # -------------------------------------------------------------
    # SLIDE 6: Benchmark Results & Empirical Evaluation
    # -------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s6)
    add_header(s6, "Validation & Testing", "Empirical Dataset Benchmark & Quality Assurance")

    add_card(s6, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8), 
             "50-Document Real-World Benchmark",
             [
                 "Invoices (20 docs): 100% Extraction Rate | 100% Math Pass Rate | 96.2% Confidence",
                 "Balance Sheets (10 docs): 100% Extraction Rate | 100% Math Pass Rate | 94.8% Confidence",
                 "Profit & Loss (10 docs): 100% Extraction Rate | 100% Math Pass Rate | 95.1% Confidence",
                 "Cash Flow (10 docs): 100% Extraction Rate | Discrepancy Audited | 95.5% Confidence",
                 "Overall Platform Performance: 100% Operational, 95.4% Mean Confidence across all 50 files.",
                 "Automated benchmark executable anytime via: python scripts/benchmark_dataset.py."
             ], COLOR_PRIMARY)

    add_card(s6, Inches(6.8), Inches(1.8), Inches(5.6), Inches(4.8), 
             "Automated Test Suite & Code Quality",
             [
                 "10/10 Automated Pytest Tests Passing (100% coverage of core endpoints and math engines).",
                 "Unit tests for Invoice math checks, Balance Sheet equations, and Cash Flow reconciliation.",
                 "Integration tests for file ingestion, validation errors, and health check endpoints.",
                 "CI/CD and container validation with multi-stage Docker build."
             ], COLOR_ACCENT)

    # -------------------------------------------------------------
    # SLIDE 7: Technology Stack & Production Deployment
    # -------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_slide_layout)
    set_slide_background(s7)
    add_header(s7, "Tech Stack & Deployment", "Production Readiness & Deployment Architecture")

    add_card(s7, Inches(0.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "Core Backend Stack",
             [
                 "Python 3.11+ Runtime",
                 "FastAPI (High-performance async ASGI framework)",
                 "Uvicorn (Lightning-fast ASGI web server)",
                 "Pydantic v2 (Strict data contract validation)",
                 "SQLAlchemy 2.0 (Relational ORM for audit persistence)"
             ], COLOR_PRIMARY)

    add_card(s7, Inches(4.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "Computer Vision & OCR",
             [
                 "pypdfium2 (Direct PDF rasterization & vector text parser)",
                 "RapidOCR with ONNX Runtime (CPU-optimized neural OCR)",
                 "Pillow (Image pre-processing & enhancement)",
                 "Zero external C++ binary dependencies"
             ], COLOR_PRIMARY)

    add_card(s7, Inches(8.8), Inches(1.8), Inches(3.6), Inches(4.8), 
             "Cloud & Deployment",
             [
                 "Containerized with Docker (multi-stage lightweight container)",
                 "Live Production Deployment on Render Cloud",
                 "Health Check Monitoring endpoint (/health)",
                 "Automated Swagger API Docs (/docs)",
                 "Public GitHub Repo with full open-source documentation"
             ], COLOR_ACCENT)

    prs.save(output_path)
    print(f"Presentation saved successfully to {output_path}")

if __name__ == "__main__":
    create_presentation()
