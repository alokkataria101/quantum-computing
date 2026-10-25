"""app/pdf_processor.py – PyMuPDF text extraction and optional OCR."""

from __future__ import annotations

import io
import logging
import re
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


# ── Figure caption pattern ────────────────────────────────────────────────────
# Matches "Figure 8.10", "Fig. 3.1", "Figure 26.1a" etc.
_FIG_CAPTION_RE = re.compile(
    r'^\s*(?:Figure|Fig\.?)\s*(\d+[\.\-]\d+[a-z]?)\s*$', re.I
)

# Also used by the template JS to detect figure references in question text
FIG_REF_RE_STR = r'\b(?:figure|fig\.?)\s*\(?(\d+[\.\-]\d+[a-z]?)\)?'


def extract_figures(pdf_path: Path, pad_pts: float = 10.0) -> list[dict]:
    """
    Scan every page of the PDF for figure caption blocks ("Figure N.M").
    For each caption found, compute the bounding box of the figure above it
    (the vertical gap in that column between the preceding text block and the
    caption label itself).

    Returns a list of dicts:
        fig_num   – normalised label, e.g. "8.10"
        page      – 1-based page number
        bbox      – (x0, y0, x1, y1) in PDF points
    """
    if not FITZ_AVAILABLE:
        raise RuntimeError("PyMuPDF is not installed.")

    doc = fitz.open(str(pdf_path))
    results: list[dict] = []

    for pg_idx in range(doc.page_count):
        page = doc[pg_idx]
        page_rect = page.rect
        pw, ph = page_rect.width, page_rect.height
        mid = pw / 2

        # All text blocks on this page, sorted top→bottom
        blocks = [
            (b[0], b[1], b[2], b[3], b[4])   # x0,y0,x1,y1,text
            for b in page.get_text("blocks")
            if b[6] == 0 and b[3] - b[1] > 2  # text blocks only
        ]
        blocks.sort(key=lambda b: b[1])

        for idx, (cx0, cy0, cx1, cy1, text) in enumerate(blocks):
            m = _FIG_CAPTION_RE.match(text)
            if not m:
                continue

            fig_num = m.group(1).replace('-', '.')  # normalise separator
            caption_top = cy0   # caption label starts here
            caption_y1  = cy1

            # Determine which column this caption is in
            col_left  = cx0 < mid  # True = left column

            # Find the text block directly above this caption in the same column
            # (same column = centre-x on the same side of mid)
            above = None
            for prev_x0, prev_y0, prev_x1, prev_y1, _ in reversed(blocks[:idx]):
                prev_centre = (prev_x0 + prev_x1) / 2
                if col_left and prev_centre > mid:
                    continue   # skip right-column blocks
                if not col_left and prev_centre < mid:
                    continue   # skip left-column blocks
                if prev_y1 <= caption_top:
                    above = (prev_x0, prev_y0, prev_x1, prev_y1)
                    break

            # Figure bbox = from bottom-of-above-block to top-of-caption, full col width
            if above:
                fig_y0 = above[3]   # bottom of the preceding text block
            else:
                fig_y0 = 0.0        # top of page if nothing above

            # Column x extent: use the caption's x extent padded
            fig_x0 = max(cx0 - pad_pts, 0)
            fig_x1 = min(cx1 + pad_pts, pw)

            # Add some padding above and below
            bbox = (
                fig_x0,
                max(fig_y0 - pad_pts, 0),
                fig_x1,
                min(caption_y1 + pad_pts, ph),
            )

            # Skip degenerate boxes (less than 20pt tall)
            if bbox[3] - bbox[1] < 20:
                continue

            results.append({
                "fig_num": fig_num,
                "page":    pg_idx + 1,
                "bbox":    bbox,
            })
            logger.debug("Found Figure %s on page %d  bbox=%s", fig_num, pg_idx + 1, bbox)

    doc.close()
    return results


def render_figure_crop(
    pdf_path: Path,
    bbox: tuple[float, float, float, float],
    page_number: int,
    dpi: int = 150,
) -> bytes:
    """Render a cropped region of a PDF page to PNG bytes.
    bbox is (x0, y0, x1, y1) in PDF points. page_number is 1-based.
    """
    if not FITZ_AVAILABLE:
        raise RuntimeError("PyMuPDF is not installed.")
    doc = fitz.open(str(pdf_path))
    page = doc[page_number - 1]
    clip = fitz.Rect(*bbox).intersect(page.rect)
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat, clip=clip, alpha=False)
    png_bytes = pix.tobytes("png")
    doc.close()
    return png_bytes
