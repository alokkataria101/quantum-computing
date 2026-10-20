"""app/pdf_processor.py – PyMuPDF text extraction and optional OCR."""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import pymupdf as fitz  # PyMuPDF 2.x (fitz alias kept for internal use)
    FITZ_AVAILABLE = True
except ImportError:
    FITZ_AVAILABLE = False
    logger.warning("PyMuPDF not installed; PDF processing unavailable.")

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from .config import settings


@dataclass
class ExtractedPage:
    page_number: int        # 1-based
    text: str
    has_images: bool
    is_scanned: bool        # text layer is empty or near-empty
    ocr_used: bool


@dataclass
class PDFMeta:
    title: str
    author: str
    total_pages: int
    toc: list[list]         # PyMuPDF TOC: [[level, title, page], ...]


# ── Text density threshold to call a page "scanned" ─────────────────────────
_MIN_TEXT_CHARS = 20


def _is_scanned(text: str) -> bool:
    return len(text.strip()) < _MIN_TEXT_CHARS


def _page_to_image(page: "fitz.Page", dpi: int) -> "Image.Image":
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img


def _ocr_page(page: "fitz.Page", language: str, dpi: int) -> str:
    if not OCR_AVAILABLE:
        logger.warning("pytesseract not installed; skipping OCR for page %d", page.number + 1)
        return ""
    try:
        if settings.tesseract_cmd and settings.tesseract_cmd != "tesseract":
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd
        img = _page_to_image(page, dpi)
        return pytesseract.image_to_string(img, lang=language)
    except Exception as exc:
        logger.error("OCR failed for page %d: %s", page.number + 1, exc)
        return ""


def extract_pdf_meta(pdf_path: Path) -> PDFMeta:
    if not FITZ_AVAILABLE:
        raise RuntimeError("PyMuPDF is not installed.")
    doc = fitz.open(str(pdf_path))
    meta = doc.metadata or {}
    toc = doc.get_toc(simple=False) or []
    result = PDFMeta(
        title=meta.get("title", "") or "",
        author=meta.get("author", "") or "",
        total_pages=doc.page_count,
        toc=toc,
    )
    doc.close()
    return result


def extract_pages(
    pdf_path: Path,
    ocr_enabled: bool = True,
    ocr_language: str = "eng",
    dpi: int = 150,
) -> list[ExtractedPage]:
    """
    Extract text from every page. Falls back to OCR for scanned pages.
    Returns list of ExtractedPage in page order (1-based numbering).
    """
    if not FITZ_AVAILABLE:
        raise RuntimeError("PyMuPDF is not installed.")

    doc = fitz.open(str(pdf_path))
    results: list[ExtractedPage] = []

    for i in range(doc.page_count):
        page = doc[i]
        text = page.get_text("text")
        has_images = bool(page.get_images(full=False))
        scanned = _is_scanned(text)
        ocr_used = False

        if scanned and ocr_enabled:
            text = _ocr_page(page, ocr_language, dpi)
            ocr_used = True

        results.append(ExtractedPage(
            page_number=i + 1,
            text=text,
            has_images=has_images,
            is_scanned=scanned,
            ocr_used=ocr_used,
        ))

    doc.close()
    return results


def render_page_to_png(pdf_path: Path, page_number: int, dpi: int = 150) -> bytes:
    """
    Render a single PDF page to PNG bytes.
    page_number is 1-based.
    """
    if not FITZ_AVAILABLE:
        raise RuntimeError("PyMuPDF is not installed.")
    doc = fitz.open(str(pdf_path))
    if page_number < 1 or page_number > doc.page_count:
        doc.close()
        raise ValueError(f"Page {page_number} out of range (1–{doc.page_count}).")
    page = doc[page_number - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes
