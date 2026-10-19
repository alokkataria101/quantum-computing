"""app/routers/questions.py – question extraction endpoints."""

from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from ..database import get_db
from ..jobs import create_job, update_job
from ..models import QuestionList, QuestionRecord, QuestionType, JobRecord, JobStatus, JobType
from ..question_extractor import extract_questions_from_chapter
from ..models import ChapterRecord

router = APIRouter(tags=["questions"])


async def _get_chapter(book_id: str, chapter_id: str) -> ChapterRecord:
    db = await get_db()
    async with db.execute(
        "SELECT * FROM chapters WHERE chapter_id = ? AND book_id = ?",
        (chapter_id, book_id),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Chapter not found.")
    return ChapterRecord(
        chapter_id=row["chapter_id"], book_id=row["book_id"],
        number=row["number"], title=row["title"],
        page_start=row["page_start"], page_end=row["page_end"],
        confidence=row["confidence"], source=row["source"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/chapters/{chapter_id}/questions
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/books/{book_id}/chapters/{chapter_id}/questions",
    response_model=QuestionList,
)
async def get_questions(
    book_id: str,
    chapter_id: str,
    question_type: QuestionType | None = None,
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    db = await get_db()
    where = "book_id = ? AND chapter_id = ?"
    params: list = [book_id, chapter_id]
    if question_type:
        where += " AND question_type = ?"
        params.append(question_type.value)
    params += [limit, offset]
    async with db.execute(
        f"SELECT * FROM questions WHERE {where} ORDER BY page_start, question_number LIMIT ? OFFSET ?",
        params,
    ) as cur:
        rows = await cur.fetchall()
    questions = [_row_to_q(r) for r in rows]
    return QuestionList(questions=questions, total=len(questions), chapter_id=chapter_id)


# ─────────────────────────────────────────────────────────────────────────────
# POST /books/{book_id}/chapters/{chapter_id}/extract
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/books/{book_id}/chapters/{chapter_id}/extract",
    response_model=JobRecord,
)
async def start_extraction(book_id: str, chapter_id: str):
    chapter = await _get_chapter(book_id, chapter_id)
    db = await get_db()

    # Check book is indexed
    async with db.execute("SELECT status FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    if not brow or brow["status"] != "indexed":
        raise HTTPException(
            status_code=400,
            detail="Book must be indexed before extracting questions. Run POST /books/{id}/index first.",
        )

    job_id = await create_job(JobType.extract, book_id, chapter_id)

    async def _do_extract():
        # Load chapter pages from DB
        async with db.execute(
            "SELECT page_number, text FROM pages WHERE book_id = ? AND page_number BETWEEN ? AND ? ORDER BY page_number",
            (book_id, chapter.page_start, chapter.page_end),
        ) as cur:
            rows = await cur.fetchall()
        pages = [{"page_number": r["page_number"], "text": r["text"]} for r in rows]

        await update_job(job_id, progress=0.3, message="Extracting questions…")
        questions = extract_questions_from_chapter(book_id, chapter, pages)

        # Delete existing questions for this chapter
        await db.execute(
            "DELETE FROM questions WHERE chapter_id = ?", (chapter_id,)
        )
        # Insert new
        if questions:
            await db.executemany(
                """INSERT INTO questions
                   (question_id, book_id, chapter_id, chapter_number, question_type,
                    question_number, question_text, solution_text, answer_text,
                    page_start, page_end, confidence, extraction_method)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (q.question_id, q.book_id, q.chapter_id, q.chapter_number,
                     q.question_type.value, q.question_number, q.question_text,
                     q.solution_text, q.answer_text, q.page_start, q.page_end,
                     q.confidence, q.extraction_method)
                    for q in questions
                ],
            )
        await db.commit()
        await update_job(job_id, progress=1.0, status="done",
                         message=f"Extracted {len(questions)} items.")

    asyncio.create_task(_do_extract())

    return JobRecord(
        job_id=job_id, job_type=JobType.extract,
        book_id=book_id, chapter_id=chapter_id,
        status=JobStatus.pending, progress=0.0,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )


def _row_to_q(row) -> QuestionRecord:
    d = dict(row)
    return QuestionRecord(
        question_id=d["question_id"], book_id=d["book_id"],
        chapter_id=d["chapter_id"], chapter_number=d["chapter_number"],
        question_type=QuestionType(d["question_type"]),
        question_number=d.get("question_number"),
        question_text=d["question_text"],
        solution_text=d.get("solution_text"),
        answer_text=d.get("answer_text"),
        page_start=d["page_start"], page_end=d["page_end"],
        confidence=d["confidence"],
        extraction_method=d.get("extraction_method", "pattern"),
    )
