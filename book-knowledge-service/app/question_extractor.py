"""app/question_extractor.py – pattern-based extraction of examples and questions."""

from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Optional

from .models import ChapterRecord, QuestionRecord, QuestionType

logger = logging.getLogger(__name__)

# ── Section-header patterns ────────────────────────────────────────────────────
_SECTION_HEADERS = {
    QuestionType.worked_example:   re.compile(r"WORKED\s+OUT\s+EXAMPLES?", re.I),
    QuestionType.short_answer:     re.compile(r"QUESTIONS?\s+FOR\s+SHORT\s+ANSWER", re.I),
    QuestionType.objective_1:      re.compile(r"OBJECTIVE\s+[I1](?!\s*I)", re.I),
    QuestionType.objective_2:      re.compile(r"OBJECTIVE\s+II", re.I),
    QuestionType.exercise:         re.compile(r"^EXERCISES?$", re.I | re.MULTILINE),
}

# ── In-text example patterns ──────────────────────────────────────────────────
_INLINE_EXAMPLE = re.compile(
    r"(?:Example|Solved\s+Example)\s+(\d+[\.\d]*)",
    re.I,
)

# ── Numbered item patterns (for exercises / objectives) ──────────────────────
_NUMBERED_ITEM = re.compile(
    r"(?:^|\n)\s*(\d+)\.\s+(.{10,500}?)(?=\n\s*\d+\.\s|\Z)",
    re.S,
)

# ── Solution / Answer markers ─────────────────────────────────────────────────
_SOLUTION_HEADER = re.compile(r"Solution\s*:", re.I)
_ANSWER_HEADER   = re.compile(r"(?:Answer|Ans)\.?\s*:", re.I)


@dataclass
class _Block:
    q_type: QuestionType
    page_start: int
    page_end: int
    text: str


def _assign_chapter_to_pages(
    chapter: ChapterRecord,
    pages: list[dict],   # list of {"page_number": int, "text": str}
) -> list[dict]:
    return [p for p in pages if chapter.page_start <= p["page_number"] <= chapter.page_end]


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
        q = text[: ans_m.start()].strip()
        ans = text[ans_m.end():].strip()
        return q, None, ans

    return text.strip(), None, None


def extract_questions_from_chapter(
    book_id: str,
    chapter: ChapterRecord,
    pages: list[dict],   # [{"page_number": int, "text": str}]
) -> list[QuestionRecord]:
    """
    Extract all question/example types from the chapter's pages.
    Uses pattern matching on extracted text.
    """
    chapter_pages = _assign_chapter_to_pages(chapter, pages)
    if not chapter_pages:
        return []

    # Concatenate chapter text with page markers
    combined_blocks: list[tuple[int, str]] = []  # (page_number, text)
    for p in chapter_pages:
        combined_blocks.append((p["page_number"], p["text"]))

    results: list[QuestionRecord] = []

    # ── 1. In-text numbered examples ─────────────────────────────────────────
    for page_num, text in combined_blocks:
        for m in _INLINE_EXAMPLE.finditer(text):
            num = m.group(1)
            # Grab the text until the next example or section header (~500 chars)
            start = m.start()
            snippet = text[start: start + 800].strip()
            q_text, sol, ans = _split_solution(snippet)
            results.append(QuestionRecord(
                question_id=str(uuid.uuid4()),
                book_id=book_id,
                chapter_id=chapter.chapter_id,
                chapter_number=chapter.number,
                question_type=QuestionType.example,
                question_number=num,
                question_text=q_text[:1000],
                solution_text=sol,
                answer_text=ans,
                page_start=page_num,
                page_end=page_num,
                confidence=0.85,
                extraction_method="pattern",
            ))

    # ── 2. Worked Out Examples section ────────────────────────────────────────
    results += _extract_section(
        book_id, chapter, combined_blocks,
        _SECTION_HEADERS[QuestionType.worked_example],
        QuestionType.worked_example,
    )

    # ── 3. Questions for Short Answer ─────────────────────────────────────────
    results += _extract_section(
        book_id, chapter, combined_blocks,
        _SECTION_HEADERS[QuestionType.short_answer],
        QuestionType.short_answer,
    )

    # ── 4. Objective I ────────────────────────────────────────────────────────
    results += _extract_section(
        book_id, chapter, combined_blocks,
        _SECTION_HEADERS[QuestionType.objective_1],
        QuestionType.objective_1,
    )

    # ── 5. Objective II ───────────────────────────────────────────────────────
    results += _extract_section(
        book_id, chapter, combined_blocks,
        _SECTION_HEADERS[QuestionType.objective_2],
        QuestionType.objective_2,
    )

    # ── 6. Exercises ──────────────────────────────────────────────────────────
    results += _extract_section(
        book_id, chapter, combined_blocks,
        _SECTION_HEADERS[QuestionType.exercise],
        QuestionType.exercise,
    )

    logger.info(
        "Extracted %d items from chapter %s (%s)",
        len(results), chapter.chapter_id, chapter.title,
    )
    return results


def _extract_section(
    book_id: str,
    chapter: ChapterRecord,
    blocks: list[tuple[int, str]],
    header_pattern: re.Pattern,
    q_type: QuestionType,
) -> list[QuestionRecord]:
    """Find the section header and extract numbered items that follow it."""
    results: list[QuestionRecord] = []

    for page_num, text in blocks:
        hm = header_pattern.search(text)
        if not hm:
            continue

        section_text = text[hm.end():]

        # Try next section header to bound the section
        next_sec = re.search(
            r"\n(?:OBJECTIVE|EXERCISES?|QUESTIONS?\s+FOR|WORKED\s+OUT)",
            section_text, re.I,
        )
        if next_sec:
            section_text = section_text[: next_sec.start()]

        for m in _NUMBERED_ITEM.finditer(section_text):
            num = m.group(1)
            item_text = m.group(2).strip()
            if len(item_text) < 10:
                continue
            q_text, sol, ans = _split_solution(item_text)
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
                page_start=page_num,
                page_end=page_num,
                confidence=0.80,
                extraction_method="pattern",
            ))

    return results
