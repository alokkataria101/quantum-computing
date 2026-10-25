"""app/routers/ai.py – AI-powered endpoints using IBM watsonx.ai.

Endpoints
---------
POST /books/{book_id}/ask
    Ask a question grounded in the book's indexed text.

POST /books/{book_id}/chapters/{chapter_id}/generate-questions
    Generate well-formatted questions (MCQ / short-answer / numerical)
    with proper scientific notation from a specific chapter.

Both endpoints degrade gracefully — if watsonx credentials are not set,
they return HTTP 503 with a clear message so the rest of the service
continues to work normally.
"""

from __future__ import annotations

import json
import logging
import re

from fastapi import APIRouter, HTTPException

from ..ai_client import get_ai_client, RateLimitError
from ..database import get_db
from ..models import (
    AskRequest, AskResponse,
    GenerateQuestionsRequest, GenerateQuestionsResponse, GeneratedQuestion,
)

logger = logging.getLogger(__name__)
router = APIRouter(tags=["AI (watsonx)"])

_AI_DISABLED_MSG = (
    "IBM watsonx AI is not configured. "
    "Set WATSONX_API_KEY and WATSONX_PROJECT_ID in .env.secrets to enable AI features."
)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _get_chapter_record(book_id: str, chapter_id: str) -> dict:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM chapters WHERE chapter_id = ? AND book_id = ?",
        (chapter_id, book_id),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    return dict(row)


async def _fetch_chapter_pages(book_id: str, page_start: int, page_end: int) -> list[dict]:
    db = await get_db()
    async with db.execute(
        "SELECT page_number, text FROM pages "
        "WHERE book_id = ? AND page_number BETWEEN ? AND ? ORDER BY page_number",
        (book_id, page_start, page_end),
    ) as cur:
        rows = await cur.fetchall()
    return [{"page_number": r["page_number"], "text": r["text"]} for r in rows]


async def _fts_pages(book_id: str, query: str, chapter_id: str | None, limit: int) -> list[dict]:
    """Run FTS5 search and return top pages with their text."""
    from ..indexer import full_text_search
    hits = await full_text_search(query, book_id=book_id, chapter_id=chapter_id, limit=limit)
    if not hits:
        return []
    db = await get_db()
    page_nums = [h["page_number"] for h in hits]
    placeholders = ",".join("?" * len(page_nums))
    async with db.execute(
        f"SELECT page_number, text FROM pages WHERE book_id = ? AND page_number IN ({placeholders})",
        [book_id, *page_nums],
    ) as cur:
        rows = await cur.fetchall()
    return [{"page_number": r["page_number"], "text": r["text"]} for r in rows]


def _build_context(pages: list[dict], max_chars: int = 6000) -> tuple[str, list[int]]:
    """Concatenate page texts up to max_chars. Returns (context_text, page_numbers)."""
    parts, nums, total = [], [], 0
    for p in pages:
        txt = p["text"].strip()
        if not txt:
            continue
        if total + len(txt) > max_chars:
            txt = txt[: max_chars - total]
        parts.append(f"[Page {p['page_number']}]\n{txt}")
        nums.append(p["page_number"])
        total += len(txt)
        if total >= max_chars:
            break
    return "\n\n".join(parts), nums


# ─────────────────────────────────────────────────────────────────────────────
# POST /books/{book_id}/ask
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/books/{book_id}/ask",
    response_model=AskResponse,
    summary="Ask a question about the book (watsonx RAG)",
    description=(
        "Uses FTS5 full-text search to find the most relevant pages, then sends "
        "them as context to IBM watsonx Granite to answer the question. "
        "Requires watsonx credentials in .env.secrets."
    ),
)
async def ask_book(book_id: str, req: AskRequest):
    ai = get_ai_client()
    if not ai.is_enabled():
        raise HTTPException(status_code=503, detail=_AI_DISABLED_MSG)

    # Verify book exists
    db = await get_db()
    async with db.execute("SELECT status FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    if not brow:
        raise HTTPException(status_code=404, detail="Book not found.")
    if brow["status"] != "indexed":
        raise HTTPException(status_code=400, detail="Book must be indexed first.")

    # Retrieve relevant pages via FTS5
    pages = await _fts_pages(book_id, req.question, req.chapter_id, limit=req.max_pages)
    if not pages:
        raise HTTPException(
            status_code=404,
            detail="No relevant pages found for your question. Try indexing the book first.",
        )

    context, source_pages = _build_context(pages)

    # Chapter title if restricted
    chapter_title = None
    if req.chapter_id:
        async with db.execute(
            "SELECT title FROM chapters WHERE chapter_id = ?", (req.chapter_id,)
        ) as cur:
            crow = await cur.fetchone()
        if crow:
            chapter_title = crow["title"]

    prompt = f"""You are a physics and science tutor. Answer the student's question using ONLY the provided book text.
Use proper scientific notation: write Greek letters (α β γ θ ω λ μ π), superscripts (x², v³), subscripts (v₀, F_net),
fractions, and equations clearly. If the answer is not in the text, say so honestly.

BOOK TEXT:
{context}

STUDENT QUESTION: {req.question}

ANSWER (clear, concise, well-formatted):"""

    try:
        answer = ai.generate(prompt)
    except RateLimitError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not answer:
        raise HTTPException(status_code=500, detail="AI generation failed.")

    return AskResponse(
        question=req.question,
        answer=answer,
        source_pages=source_pages,
        chapter_title=chapter_title,
        ai_enabled=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /books/{book_id}/chapters/{chapter_id}/generate-questions
# ─────────────────────────────────────────────────────────────────────────────

_TYPE_INSTRUCTIONS = {
    "mcq": (
        "Generate ONLY multiple-choice questions. "
        "Each question must have exactly 4 options labelled (A), (B), (C), (D). "
        "Mark the correct answer."
    ),
    "short": (
        "Generate ONLY short-answer questions (2–4 lines each). "
        "No options needed."
    ),
    "numerical": (
        "Generate ONLY numerical/calculation problems. "
        "Include given data, what to find, and the numerical answer with units."
    ),
    "mixed": (
        "Generate a mix: roughly 1/3 multiple-choice (with 4 options A–D), "
        "1/3 short-answer, 1/3 numerical problems."
    ),
}

_DIFFICULTY_NOTES = {
    "easy":   "suitable for first-time learners, straightforward recall",
    "medium": "requires understanding and application of concepts",
    "hard":   "requires multi-step reasoning, derivations, or combining concepts",
}


@router.post(
    "/books/{book_id}/chapters/{chapter_id}/generate-questions",
    response_model=GenerateQuestionsResponse,
    summary="Generate AI questions from a chapter with proper notation",
    description=(
        "Reads the chapter's indexed text and asks IBM watsonx Granite to generate "
        "well-formatted questions with correct scientific notation (Greek letters, "
        "superscripts, subscripts, equations). Requires watsonx credentials."
    ),
)
async def generate_questions_ai(
    book_id: str,
    chapter_id: str,
    req: GenerateQuestionsRequest,
):
    ai = get_ai_client()
    if not ai.is_enabled():
        raise HTTPException(status_code=503, detail=_AI_DISABLED_MSG)

    ch = await _get_chapter_record(book_id, chapter_id)
    pages = await _fetch_chapter_pages(book_id, ch["page_start"], ch["page_end"])

    if not pages:
        raise HTTPException(
            status_code=404,
            detail="No indexed pages found for this chapter. Run /index first.",
        )

    context, _ = _build_context(pages, max_chars=7000)
    q_type     = req.question_type if req.question_type in _TYPE_INSTRUCTIONS else "mixed"
    type_instr = _TYPE_INSTRUCTIONS[q_type]
    diff_note  = _DIFFICULTY_NOTES.get(req.difficulty, _DIFFICULTY_NOTES["medium"])

    prompt = f"""You are an expert physics teacher creating an exam question paper.
Generate exactly {req.count} questions from the chapter text below.

RULES:
- Difficulty: {req.difficulty} ({diff_note})
- {type_instr}
- Use proper scientific notation throughout:
    * Greek letters: α (alpha), β (beta), γ (gamma), θ (theta), ω (omega), λ (lambda), μ (mu), π (pi), Δ (delta), ρ (rho), σ (sigma)
    * Superscripts: write as x², v³, m/s², kg·m²
    * Subscripts: write as v₀, a_x, F_net, m₁, m₂
    * Fractions: write as F = ma, p = mv, KE = ½mv²
    * Vectors: write as F⃗, v⃗, a⃗
- Every question must be self-contained (include all given data)
- Number questions Q1, Q2, ...

OUTPUT FORMAT (strict JSON array, nothing else):
[
  {{
    "number": 1,
    "type": "mcq|short|numerical",
    "question": "full question text",
    "options": ["(A) ...", "(B) ...", "(C) ...", "(D) ..."],
    "answer": "correct answer or solution",
    "hint": "optional hint",
    "page_start": <page number from CHAPTER TEXT where this question is based, e.g. 42>
  }}
]
For short/numerical questions, set "options" to null.
For "page_start", use the [Page N] marker nearest to the content this question references.

CHAPTER: {ch["title"]}

CHAPTER TEXT:
{context}

JSON OUTPUT:"""

    # Scale token budget: ~200 tokens per question for MCQ (options + answer), ~120 for short/numerical
    tokens_per_q = 220 if q_type in ("mcq", "mixed") else 140
    max_tokens = min(max(tokens_per_q * req.count + 200, 800), 3000)

    try:
        raw = ai.generate(prompt, max_new_tokens=max_tokens)
    except RateLimitError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    if not raw:
        raise HTTPException(status_code=500, detail="AI generation failed.")

    # Parse JSON from response (model may wrap it in markdown code fences)
    questions: list[GeneratedQuestion] = []
    try:
        # Strip markdown fences if present
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        # Find the JSON array
        m = re.search(r"\[.*\]", clean, re.S)
        if m:
            data = json.loads(m.group())
        else:
            data = json.loads(clean)

        for item in data:
            # page_start: use what AI returned; must be within the chapter range
            pg = item.get("page_start")
            if isinstance(pg, int) and ch["page_start"] <= pg <= ch["page_end"]:
                page_start = pg
            else:
                page_start = ch["page_start"]  # fall back to first page of chapter
            questions.append(GeneratedQuestion(
                number     = item.get("number", len(questions) + 1),
                type       = item.get("type", q_type),
                question   = item.get("question", ""),
                options    = item.get("options"),
                answer     = item.get("answer"),
                hint       = item.get("hint"),
                page_start = page_start,
            ))
    except Exception as exc:
        logger.warning("Failed to parse AI JSON response: %s\nRaw: %s", exc, raw[:500])
        # Return the raw text as a single question so caller still gets something
        questions = [GeneratedQuestion(
            number=1, type="raw",
            question=raw,
            options=None, answer=None, hint="AI response could not be parsed as JSON.",
        )]

    return GenerateQuestionsResponse(
        chapter_title  = ch["title"],
        chapter_number = ch["number"],
        questions      = questions,
        total          = len(questions),
        ai_enabled     = True,
    )
