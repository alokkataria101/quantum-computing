"""app/question_extractor.py – pattern-based extraction of examples and questions."""

from __future__ import annotations

import logging
import re
import uuid
from typing import Optional

from .models import ChapterRecord, QuestionRecord, QuestionType
from .pdf_processor import normalize_pdf_text

logger = logging.getLogger(__name__)

# ── Page marker injected into combined text ───────────────────────────────────
_PAGE_MARKER = "\x00PAGE:{}\x00"          # null-byte delimited, never in PDF text
_PAGE_MARKER_RE = re.compile(r"\x00PAGE:(\d+)\x00")

# ── Section-header patterns ───────────────────────────────────────────────────
_SECTION_HEADERS: dict[QuestionType, re.Pattern] = {
    QuestionType.worked_example: re.compile(r"WORKED\s+OUT\s+EXAMPLES?", re.I),
    QuestionType.short_answer:   re.compile(r"QUESTIONS?\s+FOR\s+SHORT\s+ANSWER", re.I),
    QuestionType.objective_1:    re.compile(r"OBJECTIVE\s+[I1](?!\s*I)", re.I),
    QuestionType.objective_2:    re.compile(r"OBJECTIVE\s+II", re.I),
    QuestionType.exercise:       re.compile(r"(?:^|\n)\s*EXERCISES?\s*\n", re.I),
}

# All section headers as a single alternation — used to bound sections
_ANY_SECTION_HDR = re.compile(
    r"(?:WORKED\s+OUT\s+EXAMPLES?|QUESTIONS?\s+FOR\s+SHORT\s+ANSWER"
    r"|OBJECTIVE\s+(?:I{1,2}|1|2)|EXERCISES?)\s*\n",
    re.I,
)

# ── In-text example patterns ──────────────────────────────────────────────────
_INLINE_EXAMPLE = re.compile(
    r"(?:^|\n)\s*(?:Solved\s+)?Example\s+(\d+[\.\d]*)\b",
    re.I,
)

# ── Numbered item: "1. text"  or  "1.  text" ─────────────────────────────────
# Captures number and everything up to the next numbered item or section header
_NUMBERED_ITEM = re.compile(
    r"(?:^|\n)\s*(\d+)\.\s{1,4}(.+?)(?=\n\s*\d+\.\s|\Z|"
    r"WORKED\s+OUT|QUESTIONS?\s+FOR|OBJECTIVE\s+[I12]|EXERCISES?\s*\n)",
    re.S | re.I,
)

# ── Solution / Answer markers ─────────────────────────────────────────────────
_SOLUTION_HEADER = re.compile(r"\bSolution\s*:", re.I)
_ANSWER_HEADER   = re.compile(r"\b(?:Answer|Ans)\.?\s*:", re.I)


def _split_solution(text: str) -> tuple[str, Optional[str], Optional[str]]:
    """Split a block into (question_text, solution_text, answer_text)."""
    sol_m = _SOLUTION_HEADER.search(text)
    ans_m = _ANSWER_HEADER.search(text)
    if sol_m:
        q = text[: sol_m.start()].strip()
        rest = text[sol_m.end():]
        if ans_m and ans_m.start() > sol_m.start():
            sol = text[sol_m.end(): ans_m.start()].strip()
            ans = text[ans_m.end():].strip()
        else:
            sol = rest.strip()
            ans = None
        return q, sol, ans
    if ans_m:
        return text[: ans_m.start()].strip(), None, text[ans_m.end():].strip()
    return text.strip(), None, None


def _page_at(combined: str, pos: int, default: int) -> int:
    """Return the page number of the most recent page marker before `pos`."""
    last = default
    for m in _PAGE_MARKER_RE.finditer(combined, 0, pos):
        last = int(m.group(1))
    return last


def _strip_markers(text: str) -> str:
    """Remove page markers from a text snippet."""
    return _PAGE_MARKER_RE.sub("", text)


def extract_questions_from_chapter(
    book_id: str,
    chapter: ChapterRecord,
    pages: list[dict],   # [{"page_number": int, "text": str}]
) -> list[QuestionRecord]:
    """
    Extract all question/example types from the chapter pages.

    Builds one combined string with embedded page markers so that
    sections and questions that span page boundaries are handled correctly.
    """
    chapter_pages = sorted(
        [p for p in pages if chapter.page_start <= p["page_number"] <= chapter.page_end],
        key=lambda p: p["page_number"],
    )
    if not chapter_pages:
        return []

    # Build one combined string with page markers
    parts: list[str] = []
    for p in chapter_pages:
        parts.append(_PAGE_MARKER.format(p["page_number"]))
        parts.append(normalize_pdf_text(p["text"]))
    combined = "\n".join(parts)
    first_page = chapter_pages[0]["page_number"]

    results: list[QuestionRecord] = []

    # ── 1. In-text numbered examples ─────────────────────────────────────────
    for m in _INLINE_EXAMPLE.finditer(combined):
        num = m.group(1)
        start = m.start()
        snippet_raw = combined[start: start + 1000]
        snippet = _strip_markers(snippet_raw)
        q_text, sol, ans = _split_solution(snippet)
        if not q_text or len(q_text) < 5:
            continue
        pg = _page_at(combined, start, first_page)
        results.append(QuestionRecord(
            question_id=str(uuid.uuid4()),
            book_id=book_id,
            chapter_id=chapter.chapter_id,
            chapter_number=chapter.number,
            question_type=QuestionType.example,
            question_number=num,
            question_text=q_text[:1200],
            solution_text=sol,
            answer_text=ans,
            page_start=pg,
            page_end=pg,
            confidence=0.85,
            extraction_method="pattern",
        ))

    # ── 2–6. Named sections ───────────────────────────────────────────────────
    _SECTION_ORDER = [
        QuestionType.worked_example,
        QuestionType.short_answer,
        QuestionType.objective_1,
        QuestionType.objective_2,
        QuestionType.exercise,
    ]

    for q_type in _SECTION_ORDER:
        results += _extract_section(book_id, chapter, combined, first_page, q_type)

    # Sort by page then question number (numeric where possible)
    def _sort_key(q: QuestionRecord):
        try:
            n = int(q.question_number or "0")
        except ValueError:
            n = 0
        type_order = {
            QuestionType.example: 0,
            QuestionType.worked_example: 1,
            QuestionType.short_answer: 2,
            QuestionType.objective_1: 3,
            QuestionType.objective_2: 4,
            QuestionType.exercise: 5,
        }
        return (q.page_start, type_order.get(q.question_type, 9), n)

    results.sort(key=_sort_key)

    logger.info(
        "Extracted %d items from chapter %s (%s)",
        len(results), chapter.chapter_id, chapter.title,
    )
    return results


def _extract_section(
    book_id: str,
    chapter: ChapterRecord,
    combined: str,
    first_page: int,
    q_type: QuestionType,
) -> list[QuestionRecord]:
    """
    Find the section header in the combined chapter text and extract
    all numbered items that follow it, up to the next section header.
    Page numbers are derived from the embedded page markers.
    """
    header_pattern = _SECTION_HEADERS[q_type]
    hm = header_pattern.search(combined)
    if not hm:
        return []

    section_start = hm.end()

    # Bound section by the next section header
    next_hm = _ANY_SECTION_HDR.search(combined, section_start)
    section_end = next_hm.start() if next_hm else len(combined)
    section_text = combined[section_start:section_end]

    results: list[QuestionRecord] = []
    for m in _NUMBERED_ITEM.finditer(section_text):
        num = m.group(1)
        item_raw = m.group(2).strip()
        item_text = _strip_markers(item_raw)
        if len(item_text) < 10:
            continue
        q_text, sol, ans = _split_solution(item_text)
        if not q_text or len(q_text) < 5:
            continue

        # Page number = most recent marker before this match in the full combined string
        abs_pos = section_start + m.start()
        pg = _page_at(combined, abs_pos, first_page)

        results.append(QuestionRecord(
            question_id=str(uuid.uuid4()),
            book_id=book_id,
            chapter_id=chapter.chapter_id,
            chapter_number=chapter.number,
            question_type=q_type,
            question_number=num,
            question_text=q_text[:1500],
            solution_text=sol,
            answer_text=ans,
            page_start=pg,
            page_end=pg,
            confidence=0.80,
            extraction_method="pattern",
        ))

    return results
