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


def render_page_figures(pdf_path: Path, page_number: int, dpi: int = 150, padding: int = 8) -> bytes | None:
    """
    Return a PNG containing only the image/figure regions on the given page.

    Uses PyMuPDF's get_images() to find embedded raster images and
    get_drawings() to find vector figure blocks, then unions their bounding
    boxes, pads slightly, and renders that clip region at the requested DPI.

    Returns None if no images or figures are found (caller should fall back
    to the full-page render).
    page_number is 1-based.
    """
    if not FITZ_AVAILABLE:
        raise RuntimeError("PyMuPDF is not installed.")
    doc = fitz.open(str(pdf_path))
    if page_number < 1 or page_number > doc.page_count:
        doc.close()
        raise ValueError(f"Page {page_number} out of range (1–{doc.page_count}).")
    page = doc[page_number - 1]
    page_rect = page.rect  # full page in pts

    boxes: list["fitz.Rect"] = []

    # 1. Embedded raster images — each has a bbox on the page
    for img_info in page.get_image_info(xrefs=True):
        r = fitz.Rect(img_info["bbox"])
        if r.is_valid and not r.is_empty and r.get_area() > 100:
            boxes.append(r)

    # 2. Large vector drawing blocks (figures, graphs) — skip tiny decorations
    for path in page.get_drawings():
        r = fitz.Rect(path["rect"])
        if r.is_valid and not r.is_empty and r.get_area() > 2000:
            boxes.append(r)

    doc.close()

    if not boxes:
        return None  # no figures found

    # Union all boxes into one bounding rect
    union = boxes[0]
    for b in boxes[1:]:
        union |= b

    # Add padding (in pts) and clamp to page
    pad = padding * 72 / dpi  # convert px padding to pts at render dpi
    clip = fitz.Rect(
        max(union.x0 - pad, page_rect.x0),
        max(union.y0 - pad, page_rect.y0),
        min(union.x1 + pad, page_rect.x1),
        min(union.y1 + pad, page_rect.y1),
    )

    doc2 = fitz.open(str(pdf_path))
    page2 = doc2[page_number - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page2.get_pixmap(matrix=mat, clip=clip, alpha=False)
    png_bytes = pix.tobytes("png")
    doc2.close()
    return png_bytes
