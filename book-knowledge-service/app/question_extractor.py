"""app/question_extractor.py – 3-layer extraction of questions and visual PDF crops."""

from __future__ import annotations

import hashlib
import logging
import re
import uuid
from typing import Optional

import pymupdf as fitz

from .models import (
    BoundingBox,
    ChapterRecord,
    DifficultyLevel,
    QuestionRecord,
    QuestionType,
    ReviewStatus,
)
from .pdf_processor import normalize_pdf_text
from .storage import book_path, question_crop_path

logger = logging.getLogger(__name__)

# ── Page marker injected into combined text ───────────────────────────────────
_PAGE_MARKER = "\x00PAGE:{}\x00"          # null-byte delimited, never in PDF text
_PAGE_MARKER_RE = re.compile(r"\x00PAGE:(\d+)\x00")

# ── Section-header patterns ───────────────────────────────────────────────────
_SECTION_HEADERS: dict[QuestionType, re.Pattern] = {
    QuestionType.worked_example: re.compile(r"(?:WORKED\s+OUT\s+EXAMPLES?|SOLVED\s+EXAMPLES?|SAMPLE\s+PROBLEMS?)", re.I),
    QuestionType.short_answer:   re.compile(r"(?:QUESTIONS?\s+FOR\s+SHORT\s+ANSWER|SHORT\s+ANSWER\s+QUESTIONS?|VERY\s+SHORT\s+ANSWER\s+QUESTIONS?)", re.I),
    QuestionType.objective_1:    re.compile(r"(?:OBJECTIVE\s+[I1](?!\s*I)|MULTIPLE\s+CHOICE\s+QUESTIONS?(?:\s*-\s*I)?|MCQS?\s*-\s*I)", re.I),
    QuestionType.objective_2:    re.compile(r"(?:OBJECTIVE\s+II|MULTIPLE\s+CHOICE\s+QUESTIONS?\s*-\s*II|MCQS?\s*-\s*II)", re.I),
    QuestionType.exercise:       re.compile(r"(?:(?:^|\n)\s*(?:EXERCISES?|PRACTICE\s+PROBLEMS?|PRACTICE\s+QUESTIONS?|CHAPTER\s+EXERCISES?|PROBLEMS?|CONCEPTUAL\s+QUESTIONS?|REVIEW\s+QUESTIONS?)(?:\s+[\d\.]+|\s*[-–:]\s*[\w\d]+)?(?:\s*\n|\s{2,}))", re.I),
}

# All section headers as a single alternation — used to bound sections
_ANY_SECTION_HDR = re.compile(
    r"(?:WORKED\s+OUT\s+EXAMPLES?|SOLVED\s+EXAMPLES?|QUESTIONS?\s+FOR\s+SHORT\s+ANSWER|SHORT\s+ANSWER\s+QUESTIONS?"
    r"|OBJECTIVE\s+(?:I{1,2}|1|2)|MULTIPLE\s+CHOICE\s+QUESTIONS?|EXERCISES?|PRACTICE\s+QUESTIONS?|PROBLEMS?)\s*(?:\n|\s{2,})",
    re.I,
)

# ── In-text example patterns ──────────────────────────────────────────────────
_INLINE_EXAMPLE = re.compile(
    r"(?:^|\n)\s*(?:Solved\s+)?Example\s+(\d+[\.\d]*)\b",
    re.I,
)

# ── Numbered item: "1. text" or "Q1. text" or "1) text" ─────────────────────
# Captures number and everything up to the next numbered item or section header
_NUMBERED_ITEM = re.compile(
    r"(?:^|\n)\s*(?:(?:Q(?:uestion)?|Problem)\.?\s*|\(?\b)(\d+(?:[\.\-]\d+)?)\s*[\.\):\-]\s{1,4}(.+?)"
    r"(?=\n\s*(?:(?:Q(?:uestion)?|Problem)\.?\s*|\(?\b)\d+(?:[\.\-]\d+)?\s*[\.\):\-]\s|\Z|"
    r"WORKED\s+OUT|SOLVED\s+EXAMPLES?|QUESTIONS?\s+FOR|OBJECTIVE\s+[I12]|EXERCISES?|PRACTICE\s+QUESTIONS?|PROBLEMS?)",
    re.S | re.I,
)

# ── Solution / Answer markers ─────────────────────────────────────────────────
_SOLUTION_HEADER = re.compile(r"\bSolution\s*:", re.I)
_ANSWER_HEADER   = re.compile(r"\b(?:Answer|Ans)\.?\s*:", re.I)

# ── MCQ Options Regex ─────────────────────────────────────────────────────────
_OPTION_PATTERN = re.compile(
    r"(?:^|\n|\s{2,})(?:\(([A-Da-d1-4])\)|([A-Da-d])\.)\s+([^\n\(\)]+)",
    re.M,
)

_TRUE_FALSE_RE = re.compile(r"\b(True\s*or\s*False|State\s+whether\s+true\s+or\s+false)\b", re.I)
_FILL_BLANKS_RE = re.compile(r"(?:_{3,}|\.{4,}|\bfill\s+in\s+the\s+blank[s]?\b)", re.I)
_MATCH_FOLLOWING_RE = re.compile(r"\bmatch\s+(?:the\s+following|column\s+[ab]|items)\b", re.I)
_ASSERTION_RE = re.compile(r"\b(Assertion\s*\(?A\)?|Reason\s*\(?R\)?)\b", re.I)
_NUMERICAL_RE = re.compile(r"\b(calculate|find\s+the\s+value|determine|magnitude|velocity|acceleration|force|mass|kg|m/s|joules|watts|newton)\b", re.I)


def _extract_options(text: str) -> tuple[str, list[str]]:
    """Extract MCQ options (A, B, C, D) and return (stem_text, [options])."""
    matches = list(_OPTION_PATTERN.finditer(text))
    if len(matches) >= 2:
        first_match_start = matches[0].start()
        stem = text[:first_match_start].strip()
        options = []
        for m in matches:
            opt_letter = m.group(1) or m.group(2)
            opt_text = m.group(3).strip()
            options.append(f"({opt_letter.upper()}) {opt_text}")
        return stem, options
    return text.strip(), []


def _detect_refined_type(
    base_type: QuestionType,
    text: str,
    options: list[str],
) -> QuestionType:
    """Refine QuestionType into mcq, true_false, fill_in_the_blanks, numerical, etc."""
    if options or base_type in (QuestionType.objective_1, QuestionType.objective_2):
        return QuestionType.mcq
    if _TRUE_FALSE_RE.search(text):
        return QuestionType.true_false
    if _FILL_BLANKS_RE.search(text):
        return QuestionType.fill_in_the_blanks
    if _MATCH_FOLLOWING_RE.search(text):
        return QuestionType.match_the_following
    if _ASSERTION_RE.search(text):
        return QuestionType.assertion_reason
    if base_type == QuestionType.short_answer:
        return QuestionType.short_answer
    if _NUMERICAL_RE.search(text) and len(text) > 40:
        return QuestionType.numerical
    return base_type


def _estimate_metadata(
    q_type: QuestionType,
    text: str,
    options: list[str],
) -> tuple[DifficultyLevel, int]:
    """Estimate difficulty and default marks based on type and complexity."""
    if q_type in (QuestionType.mcq, QuestionType.true_false, QuestionType.fill_in_the_blanks):
        return DifficultyLevel.easy, 1
    if q_type in (QuestionType.short_answer, QuestionType.match_the_following):
        return DifficultyLevel.medium, 2
    if q_type == QuestionType.assertion_reason:
        return DifficultyLevel.hard, 2
    if q_type in (QuestionType.numerical, QuestionType.worked_example, QuestionType.example):
        return DifficultyLevel.medium if len(text) < 150 else DifficultyLevel.hard, 3
    if q_type == QuestionType.long_answer:
        return DifficultyLevel.hard, 5
    return DifficultyLevel.medium, 1


def _compute_hash(text: str) -> str:
    """Compute content hash for deduplication."""
    clean = re.sub(r"\s+", " ", text.lower().strip())
    return hashlib.sha256(clean.encode("utf-8")).hexdigest()[:16]


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


def crop_question_box_and_save(
    book_id: str,
    question_id: str,
    page_number: int,
    snippet_text: str,
) -> tuple[Optional[BoundingBox], Optional[str], Optional[str]]:
    """
    Locates question on page and renders an exact PNG image crop (Layer A).
    Saves image under storage/crops/{question_id}.png and returns (bounding_box, image_url, image_path).
    """
    pdf_p = book_path(book_id)
    if not pdf_p.exists():
        return None, None, None

    try:
        doc = fitz.open(str(pdf_p))
        if page_number < 1 or page_number > len(doc):
            doc.close()
            return None, None, None

        page = doc[page_number - 1]
        p_rect = page.rect

        # Search for first 5-8 words of snippet
        words = snippet_text.split()[:8]
        search_str = " ".join(words) if words else ""
        rects = page.search_for(search_str) if search_str else []

        if not rects and len(words) > 3:
            rects = page.search_for(" ".join(words[:4]))

        if rects:
            r0 = rects[0]
            # Create a clean crop box bounded within page width and reasonable height
            x0 = max(0.0, r0.x0 - 15.0)
            y0 = max(0.0, r0.y0 - 10.0)
            x1 = min(p_rect.width, r0.x1 + 320.0)
            y1 = min(p_rect.height, r0.y1 + 180.0)
            clip = fitz.Rect(x0, y0, x1, y1)
        else:
            # Fallback crop: full width of page with default height band
            x0, y0 = 0.0, 50.0
            x1, y1 = p_rect.width, min(p_rect.height, 250.0)
            clip = fitz.Rect(x0, y0, x1, y1)

        dest_png = question_crop_path(question_id)
        dest_png.parent.mkdir(parents=True, exist_ok=True)

        pix = page.get_pixmap(clip=clip, dpi=160, colorspace=fitz.csRGB)
        pix.save(str(dest_png))
        doc.close()

        bb = BoundingBox(x0=clip.x0, y0=clip.y0, x1=clip.x1, y1=clip.y1)
        image_url = f"/crops/{question_id}.png"
        return bb, image_url, str(dest_png)
    except Exception as exc:
        logger.debug("Could not crop question %s: %s", question_id, exc)
        return None, None, None


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
        q_id = str(uuid.uuid4())
        stem, opts = _extract_options(q_text)
        final_type = _detect_refined_type(QuestionType.example, stem, opts)
        diff, marks = _estimate_metadata(final_type, stem, opts)
        c_hash = _compute_hash(stem)
        bb, img_url, img_path = crop_question_box_and_save(book_id, q_id, pg, stem)

        results.append(QuestionRecord(
            question_id=q_id,
            book_id=book_id,
            chapter_id=chapter.chapter_id,
            chapter_number=chapter.number,
            question_type=final_type,
            question_number=num,
            question_text=stem[:1200],
            options=opts,
            solution_text=sol,
            answer_text=ans,
            page_start=pg,
            page_end=pg,
            confidence=0.85,
            extraction_method="pattern",
            bounding_box=bb,
            image_url=img_url,
            image_path=img_path,
            difficulty=diff,
            marks=marks,
            content_hash=c_hash,
            chapter_title=chapter.title,
            review_status=ReviewStatus.pending,
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
        q_id = str(uuid.uuid4())
        stem, opts = _extract_options(q_text)
        final_type = _detect_refined_type(q_type, stem, opts)
        diff, marks = _estimate_metadata(final_type, stem, opts)
        c_hash = _compute_hash(stem)
        bb, img_url, img_path = crop_question_box_and_save(book_id, q_id, pg, stem)

        results.append(QuestionRecord(
            question_id=q_id,
            book_id=book_id,
            chapter_id=chapter.chapter_id,
            chapter_number=chapter.number,
            question_type=final_type,
            question_number=num,
            question_text=stem[:1500],
            options=opts,
            solution_text=sol,
            answer_text=ans,
            page_start=pg,
            page_end=pg,
            confidence=0.80,
            extraction_method="pattern",
            bounding_box=bb,
            image_url=img_url,
            image_path=img_path,
            difficulty=diff,
            marks=marks,
            content_hash=c_hash,
            chapter_title=chapter.title,
            review_status=ReviewStatus.pending,
        ))

    return results
