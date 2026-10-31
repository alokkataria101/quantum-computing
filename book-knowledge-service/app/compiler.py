"""app/compiler.py – compile a questions-PDF and/or notes-PDF from the book pages.

No AI is used: every item is a cropped image from the original PDF page so
figures, equations and diagrams are preserved exactly as printed.

Notes mode
----------
Renders the body of each chapter page-by-page as a full-column image strip,
grouped by chapter with headings.  This gives a visual summary of all content.

Questions mode
--------------
Delegates to the existing ``build_book_pdf`` pipeline in ``question_pdf.py``
which crops individual questions (Examples, Exercises, Short-Answer, …) into
two-column cards.

Both
----
Produces two separate PDFs (notes + questions) and merges them into one output
file with a divider page.
"""

from __future__ import annotations

import io
import logging
import unicodedata
from pathlib import Path
from typing import Callable, Optional

import pymupdf as fitz
from PIL import Image

from .config import settings
from .models import CompileMode
from .question_pdf import (
    ChapterSpec,
    ascii_text,
    build_book_pdf,
    detect_layout,
    read_page,
    HEAD_FRAC,
    FOOT_FRAC,
    W,
    H,
    MARGIN,
    TOP,
    BOTTOM,
)

logger = logging.getLogger(__name__)

# ── helpers ───────────────────────────────────────────────────────────────────

def _chapter_specs_from_rows(rows) -> list[ChapterSpec]:
    """Convert chapter DB rows (dicts / sqlite3.Row) into ChapterSpec objects,
    filtering out front-matter and answer appendices."""
    import re
    specs = []
    for r in rows:
        # The number printed in the book (matches example labels like "23.4"); the
        # sequential `number` is only for listing chapters in the app.
        number = r["printed_number"] if "printed_number" in r.keys() and r["printed_number"] else r["number"]
        title  = re.sub(r"\s+", " ", r["title"]).strip()
        # Skip front-matter (number 0) and back-matter
        if r["number"] == 0:
            continue
        if re.match(r"(?i)(front matter|answers and appendices|appendix|index)", title):
            continue
        if title.isupper():
            title = title.title()
        specs.append(ChapterSpec(
            number=number,
            title=title,
            page_start=r["page_start"],
            page_end=r["page_end"],
        ))
    return specs


# ── notes PDF ─────────────────────────────────────────────────────────────────

_NOTES_DPI = 130        # lower than questions – full-page images
_NOTES_BODY_PAD = 6     # pts of padding around each page image


def _render_notes_page(page, layout, dpi: int = _NOTES_DPI) -> Image.Image:
    """Render the body area of a single PDF page (strips running head/foot)."""
    h = page.rect.height
    clip = fitz.Rect(0, h * HEAD_FRAC, page.rect.width, h * FOOT_FRAC)
    pix = page.get_pixmap(clip=clip, dpi=dpi, colorspace=fitz.csRGB)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def build_notes_pdf(
    src_pdf: Path,
    out_pdf: Path,
    specs: list[ChapterSpec],
    book_title: str,
    dpi: int = _NOTES_DPI,
    progress: Callable[[str], None] = print,
) -> dict:
    """Produce a notes PDF: each chapter gets a heading page followed by all its
    body pages rendered as images, one image per row, full-width on A4."""
    src = fitz.open(src_pdf)
    layout = detect_layout(src)

    out = fitz.open()
    toc: list[list] = []

    # Title page
    tp = out.new_page(width=W, height=H)
    from .question_pdf import _insert_logo
    _insert_logo(tp, W / 2 - 44, 30, 88)       # centred logo
    tp.insert_text((MARGIN, 138), ascii_text(book_title), fontsize=22, fontname="hebo")
    tp.insert_text((MARGIN, 162), "Chapter Notes — rendered from original pages",
                   fontsize=11, fontname="helv")
    tp.insert_text((MARGIN, 178), "Sri Ganesh School", fontsize=9, fontname="helv",
                   color=(0.25, 0.35, 0.55))

    usable_w = W - 2 * MARGIN

    for sp in specs:
        progress(f"Notes: chapter {sp.number} {sp.title} "
                 f"(pp {sp.page_start}–{sp.page_end})")
        # Chapter heading page
        cp = out.new_page(width=W, height=H)
        cp.insert_text((MARGIN, TOP + 16),
                       ascii_text(f"Chapter {sp.number}"), fontsize=13, fontname="hebo",
                       color=(0.18, 0.35, 0.65))
        cp.insert_text((MARGIN, TOP + 34),
                       ascii_text(sp.title), fontsize=16, fontname="hebo")
        cp.draw_line((MARGIN, TOP + 42), (W - MARGIN, TOP + 42), width=0.8)
        pg_label = f"Source pages {sp.page_start}–{sp.page_end}"
        cp.insert_text((MARGIN, TOP + 54), ascii_text(pg_label),
                       fontsize=9, fontname="helv", color=(0.45, 0.45, 0.45))
        toc.append([1, ascii_text(f"Chapter {sp.number}: {sp.title}"),
                    cp.number + 1])

        cur_page: Optional[fitz.Page] = None
        y = TOP

        def new_out_page():
            nonlocal cur_page, y
            cur_page = out.new_page(width=W, height=H)
            y = TOP

        new_out_page()

        for pno in range(sp.page_start, min(sp.page_end, src.page_count) + 1):
            img = _render_notes_page(src[pno - 1], layout, dpi)
            nat_w, nat_h = img.width * 72 / dpi, img.height * 72 / dpi
            scale = usable_w / nat_w
            w_pt  = usable_w
            h_pt  = nat_h * scale

            avail = BOTTOM - y - _NOTES_BODY_PAD
            if h_pt > avail and y > TOP:
                new_out_page()
                avail = BOTTOM - TOP

            if h_pt > avail:
                # page too tall even on fresh page — shrink further
                scale  = avail / nat_h
                w_pt   = nat_w * scale
                h_pt   = avail

            buf = io.BytesIO()
            img.save(buf, "JPEG", quality=78, optimize=True)
            cur_page.insert_image(
                fitz.Rect(MARGIN, y, MARGIN + w_pt, y + h_pt),
                stream=buf.getvalue(),
            )
            # small page-number label
            cur_page.insert_text(
                (MARGIN + w_pt + 4, y + h_pt - 4),
                f"p.{pno}", fontsize=6.5, fontname="helv", color=(0.6, 0.6, 0.6),
            )
            y += h_pt + _NOTES_BODY_PAD

    out.set_toc(toc)
    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_pdf, garbage=3, deflate=True)
    progress(f"Notes PDF: wrote {out_pdf} ({out.page_count} pages)")
    return {"pages": out.page_count}


# ── combined (both) PDF ───────────────────────────────────────────────────────

def _divider_page(out: fitz.Document, label: str) -> None:
    p = out.new_page(width=W, height=H)
    p.insert_text((MARGIN, H / 2 - 10), ascii_text(label),
                  fontsize=22, fontname="hebo", color=(0.15, 0.3, 0.6))
    p.draw_line((MARGIN, H / 2 + 6), (W - MARGIN, H / 2 + 6), width=1.2)


def _append_pdf(dest: fitz.Document, src_path: Path) -> None:
    src = fitz.open(src_path)
    dest.insert_pdf(src)
    src.close()


# ── public entry point ────────────────────────────────────────────────────────

def compile_pdf(
    book_id: str,
    chapter_rows: list,          # DB rows for selected chapters
    mode: CompileMode,
    out_path: Path,
    book_title: str,
    progress: Callable[[str], None] = print,
    dpi: int = 170,
) -> dict:
    """
    Build the requested PDF(s) and write the final file to *out_path*.

    Returns a dict with summary stats.
    """
    from .storage import book_path

    src_pdf = book_path(book_id)
    specs   = _chapter_specs_from_rows(chapter_rows)

    if not specs:
        raise ValueError("No chapter specifications found for the selected chapters.")

    tmp = out_path.parent
    tmp.mkdir(parents=True, exist_ok=True)

    stats: dict = {}

    if mode == CompileMode.questions:
        stats = build_book_pdf(src_pdf, out_path, specs, book_title,
                               dpi=dpi, progress=progress)

    elif mode == CompileMode.notes:
        stats = build_notes_pdf(src_pdf, out_path, specs, book_title,
                                dpi=dpi, progress=progress)

    elif mode == CompileMode.both:
        q_tmp  = out_path.with_suffix(".questions.tmp.pdf")
        n_tmp  = out_path.with_suffix(".notes.tmp.pdf")
        try:
            q_stats = build_book_pdf(src_pdf, q_tmp, specs, book_title,
                                     dpi=dpi, progress=progress)
            n_stats = build_notes_pdf(src_pdf, n_tmp, specs, book_title,
                                      dpi=dpi, progress=progress)
            merged = fitz.open()
            _divider_page(merged, "Part 1 — Chapter Notes")
            _append_pdf(merged, n_tmp)
            _divider_page(merged, "Part 2 — Questions")
            _append_pdf(merged, q_tmp)
            merged.save(out_path, garbage=3, deflate=True)
            progress(f"Combined PDF: {merged.page_count} pages → {out_path}")
            stats = {
                "pages": merged.page_count,
                "notes_pages": n_stats.get("pages", 0),
                "questions_pages": q_stats.get("pages", 0),
                "totals": q_stats.get("totals", {}),
            }
            merged.close()
        finally:
            for p in (q_tmp, n_tmp):
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass

    return stats
