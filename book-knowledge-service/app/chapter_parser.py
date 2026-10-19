"""app/chapter_parser.py – detect chapter boundaries from TOC or page text."""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass

from .models import ChapterRecord
from .pdf_processor import PDFMeta, ExtractedPage

logger = logging.getLogger(__name__)

# ── Heading patterns ──────────────────────────────────────────────────────────
_CHAPTER_PATTERNS = [
    re.compile(r"^CHAPTER\s+(\d+)\s*[:\-–]?\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^Chapter\s+(\d+)\s*[:\-–]?\s*(.+)$", re.MULTILINE),
    re.compile(r"^(\d+)\.\s{1,4}([A-Z][A-Za-z ]{4,60})$", re.MULTILINE),
]


def _slug_id(book_id: str, number: int) -> str:
    return f"{book_id}_ch{number:03d}"


def parse_chapters_from_toc(
    book_id: str,
    meta: PDFMeta,
    total_pages: int,
) -> list[ChapterRecord]:
    """
    Build chapter list from PDF bookmarks (TOC).
    Filters to top-level entries that look like chapters.
    """
    toc = meta.toc  # [[level, title, page, ...], ...]
    if not toc:
        return []

    # Keep level-1 entries (top level) that look like chapters
    chapter_entries = [e for e in toc if e[0] == 1]
    if not chapter_entries:
        chapter_entries = toc  # fall back to all levels

    chapters: list[ChapterRecord] = []
    for i, entry in enumerate(chapter_entries):
        _, title, page_start = entry[0], entry[1], entry[2]
        page_end = (
            chapter_entries[i + 1][2] - 1
            if i + 1 < len(chapter_entries)
            else total_pages
        )
        chapters.append(ChapterRecord(
            chapter_id=_slug_id(book_id, i + 1),
            book_id=book_id,
            number=i + 1,
            title=title.strip(),
            page_start=max(1, page_start),
            page_end=min(total_pages, max(page_start, page_end)),
            confidence=0.95,
            source="toc",
        ))

    return chapters


def parse_chapters_from_text(
    book_id: str,
    pages: list[ExtractedPage],
) -> list[ChapterRecord]:
    """
    Infer chapters by scanning page text for heading patterns.
    Used when the PDF has no bookmarks.
    """
    total_pages = len(pages)
    hits: list[tuple[int, int, str]] = []  # (page_number, chapter_num, title)

    for ep in pages:
        for pat in _CHAPTER_PATTERNS:
            for m in pat.finditer(ep.text):
                try:
                    num = int(m.group(1))
                    title = m.group(2).strip()
                except (IndexError, ValueError):
                    continue
                if 1 <= num <= 200 and len(title) >= 3:
                    hits.append((ep.page_number, num, title))
                    break

    # Deduplicate: keep first occurrence of each chapter number
    seen: set[int] = set()
    unique: list[tuple[int, int, str]] = []
    for page_num, ch_num, title in sorted(hits):
        if ch_num not in seen:
            seen.add(ch_num)
            unique.append((page_num, ch_num, title))

    chapters: list[ChapterRecord] = []
    for i, (page_start, ch_num, title) in enumerate(unique):
        page_end = unique[i + 1][0] - 1 if i + 1 < len(unique) else total_pages
        chapters.append(ChapterRecord(
            chapter_id=_slug_id(book_id, ch_num),
            book_id=book_id,
            number=ch_num,
            title=title,
            page_start=page_start,
            page_end=min(total_pages, page_end),
            confidence=0.75,
            source="inferred",
        ))

    return chapters


def detect_chapters(
    book_id: str,
    meta: PDFMeta,
    pages: list[ExtractedPage],
) -> list[ChapterRecord]:
    """
    Primary entry point: try TOC first, fall back to text scanning.
    Always includes a front-matter chapter (number=0) if the first chapter
    doesn't start on page 1.
    """
    chapters = parse_chapters_from_toc(book_id, meta, len(pages))

    if not chapters:
        logger.info("No TOC bookmarks found for book %s; inferring from text.", book_id)
        chapters = parse_chapters_from_text(book_id, pages)

    if not chapters:
        # Single-chapter fallback: treat whole book as one chapter
        chapters = [ChapterRecord(
            chapter_id=_slug_id(book_id, 1),
            book_id=book_id,
            number=1,
            title=meta.title or "Full Book",
            page_start=1,
            page_end=len(pages),
            confidence=0.5,
            source="inferred",
        )]

    # Prepend front matter if needed
    if chapters[0].page_start > 1:
        front = ChapterRecord(
            chapter_id=_slug_id(book_id, 0),
            book_id=book_id,
            number=0,
            title="Front Matter",
            page_start=1,
            page_end=chapters[0].page_start - 1,
            confidence=1.0,
            source="inferred",
        )
        chapters.insert(0, front)

    return chapters
