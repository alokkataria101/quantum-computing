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

# One printed contents entry:  "Chapter" / number / title (1-2 lines) / page
_CONTENTS_ENTRY = re.compile(
    r"^Chapter[ \t]*\n?[ \t]*(\d+)[ \t]*\n([^\n]+(?:\n[^\n\d][^\n]*)?)\n(\d+)[ \t]*$",
    re.MULTILINE,
)
_CONTENTS_HEADER = re.compile(r"^\s*(table\s+of\s+contents|contents)\b", re.IGNORECASE)
_SECTION_LINE = re.compile(r"^\d+\.\d+\s+\S", re.MULTILINE)       # "23.1 Hot and Cold Bodies"
_BACK_MATTER = re.compile(r"^\s*(ANSWERS|APPENDIX|INDEX)\b", re.IGNORECASE)
_CONTENTS_SCAN_PAGES = 40


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


def _head(text: str, n: int = 120) -> str:
    """Start of a page, with the PDF-font-shifted form of 'CHAPTER' undone.

    Some pages come out of the PDF as e.g. '&+$37(5 \\x16\\x13' - every character
    shifted by 29 - which is how the heading 'CHAPTER 30' is stored.
    """
    head = text[:n].lstrip("\x03 ")
    if head.startswith("&+$37(5"):
        # \x03 is the shifted space; the literal spaces are padding between glyphs.
        head = "".join(
            " " if c == "\x03" else c if c in "\r\n" else "" if c == " " else chr(ord(c) + 29)
            for c in head
        )
    return head


def parse_chapters_from_contents(
    book_id: str,
    pages: list[ExtractedPage],
) -> list[ChapterRecord]:
    """
    Build the chapter list from the book's printed Table of Contents, for PDFs
    that have no bookmarks. The contents give chapter numbers and titles; the
    real start page of each chapter is found by locating its 'CHAPTER N'
    heading, because printed page numbers differ from PDF page numbers.
    Returns [] when no usable contents page is found.
    """
    scan = pages[:_CONTENTS_SCAN_PAGES]

    # The contents run over consecutive pages from the 'Table of Contents' header.
    first = next((i for i, p in enumerate(scan) if _CONTENTS_HEADER.match(p.text)), None)
    if first is None:
        return []
    last = first
    for i in range(first + 1, len(scan)):
        t = scan[i].text
        if len(_SECTION_LINE.findall(t)) >= 3 or _CONTENTS_ENTRY.search(t):
            last = i
        else:
            break
    contents_text = "\n".join(p.text for p in scan[first:last + 1])

    entries: list[tuple[int, str]] = []
    for m in _CONTENTS_ENTRY.finditer(contents_text):
        num = int(m.group(1))
        if entries and num <= entries[-1][0]:
            continue                                   # keep numbers strictly increasing
        entries.append((num, " ".join(m.group(2).split())))
    if len(entries) < 3:
        return []

    # Locate each chapter's heading, searching forward from the contents pages.
    after = scan[last].page_number
    starts: dict[int, int] = {}
    cursor = after + 1
    for num, _title in entries:
        pat = re.compile(rf"^\s*CHAPTER\s+{num}\b", re.IGNORECASE)
        for p in pages:
            if p.page_number >= cursor and pat.match(_head(p.text)):
                starts[num] = p.page_number
                cursor = p.page_number + 1
                break
    if len(starts) < 3:
        return []

    found = [(n, t) for n, t in entries if n in starts]
    total = len(pages)
    back = next((p.page_number for p in pages
                 if p.page_number > starts[found[-1][0]] + 1 and _BACK_MATTER.match(_head(p.text))),
                None)

    chapters: list[ChapterRecord] = []
    for i, (num, title) in enumerate(found):
        end = starts[found[i + 1][0]] - 1 if i + 1 < len(found) else (back - 1 if back else total)
        chapters.append(ChapterRecord(
            chapter_id=_slug_id(book_id, num), book_id=book_id, number=num, title=title,
            page_start=starts[num], page_end=max(starts[num], end),
            confidence=0.9, source="contents",
        ))
    if back:
        chapters.append(ChapterRecord(
            chapter_id=_slug_id(book_id, found[-1][0] + 1), book_id=book_id,
            number=found[-1][0] + 1, title="Answers and Appendices",
            page_start=back, page_end=total, confidence=0.7, source="contents",
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
        logger.info("No TOC bookmarks found for book %s; trying the printed contents.", book_id)
        chapters = parse_chapters_from_contents(book_id, pages)

    if not chapters:
        logger.info("No printed contents found for book %s; inferring from text.", book_id)
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
