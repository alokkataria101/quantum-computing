"""app/routers/questions.py – question extraction, repository search, and review studio endpoints."""

from __future__ import annotations

import asyncio
import json
import random as _random
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import require_admin, require_user
from ..database import (
    get_db,
    get_question_by_id_db,
    row_to_question_record,
    search_questions_db,
    update_question_db,
)
from ..jobs import create_job, update_job
from ..models import (
    ChapterRecord,
    DifficultyLevel,
    GenerateResult,
    JobRecord,
    JobStatus,
    JobType,
    QuestionList,
    QuestionPatchRequest,
    QuestionRecord,
    QuestionSearchQuery,
    QuestionSearchResponse,
    QuestionType,
    ReviewStatus,
)
from ..question_extractor import extract_questions_from_chapter

_row_to_q = row_to_question_record

router = APIRouter(tags=["questions"], dependencies=[Depends(require_user)])


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
    questions = [row_to_question_record(r) for r in rows]
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
        try:
            await _run_extract()
        except Exception as exc:
            await update_job(job_id, status="failed", error=str(exc), message="Extraction failed.")

    async def _run_extract():
        # Load chapter pages from DB
        async with db.execute(
            "SELECT page_number, text FROM pages WHERE book_id = ? AND page_number BETWEEN ? AND ? ORDER BY page_number",
            (book_id, chapter.page_start, chapter.page_end),
        ) as cur:
            rows = await cur.fetchall()
        pages = [{"page_number": r["page_number"], "text": r["text"]} for r in rows]

        await update_job(job_id, progress=0.3, message="Extracting questions…")
        questions = await asyncio.to_thread(extract_questions_from_chapter, book_id, chapter, pages)

        # Delete existing questions for this chapter
        await db.execute(
            "DELETE FROM questions WHERE chapter_id = ?", (chapter_id,)
        )
        # Insert new with 3-layer representation fields
        if questions:
            await db.executemany(
                """INSERT INTO questions
                   (question_id, book_id, chapter_id, chapter_number, question_type,
                    question_number, question_text, solution_text, answer_text,
                    hint, options, sub_parts, page_start, page_end, confidence,
                    extraction_method, bounding_box, image_url, image_path,
                    difficulty, marks, content_hash, review_status)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                [
                    (
                        q.question_id,
                        q.book_id,
                        q.chapter_id,
                        q.chapter_number,
                        q.question_type.value,
                        q.question_number,
                        q.question_text,
                        q.solution_text,
                        q.answer_text,
                        q.hint,
                        json.dumps(q.options) if q.options else None,
                        json.dumps(q.sub_parts) if q.sub_parts else None,
                        q.page_start,
                        q.page_end,
                        q.confidence,
                        q.extraction_method,
                        json.dumps(q.bounding_box.model_dump()) if q.bounding_box else None,
                        q.image_url,
                        q.image_path,
                        q.difficulty.value,
                        q.marks,
                        q.content_hash,
                        q.review_status.value,
                    )
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
        created_at=datetime.now(timezone.utc), updated_at=datetime.now(timezone.utc),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/questions/generate
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/books/{book_id}/questions/generate",
    response_model=GenerateResult,
    dependencies=[Depends(require_admin)],
    summary="Generate N questions on a topic",
    description=(
        "Find chapters whose title matches `topic`, then return `count` questions "
        "of the given `question_type`. Use `random=true` to shuffle, `random=false` "
        "to return them in page order."
    ),
)
async def generate_questions(
    book_id: str,
    topic: str = Query(..., description="Topic keyword, e.g. 'optics', 'newton', 'thermodynamics'"),
    count: int = Query(10, ge=1, le=100, description="Number of questions to return"),
    question_type: QuestionType = Query(QuestionType.objective_1, description="Type of question"),
    randomize: bool = Query(True, alias="random", description="Shuffle results (true) or return in page order (false)"),
):
    db = await get_db()

    # 1. Find chapters whose title contains the topic keyword (case-insensitive)
    async with db.execute(
        "SELECT chapter_id FROM chapters WHERE book_id = ? AND LOWER(title) LIKE ?",
        (book_id, f"%{topic.lower()}%"),
    ) as cur:
        chapter_rows = await cur.fetchall()

    if not chapter_rows:
        raise HTTPException(
            status_code=404,
            detail=f"No chapters found matching topic '{topic}'. "
                   f"Use GET /books/{book_id}/chapters to see available chapter titles.",
        )

    chapter_ids = [r["chapter_id"] for r in chapter_rows]

    # 2. Pull questions of the requested type from those chapters
    placeholders = ",".join("?" * len(chapter_ids))
    async with db.execute(
        f"""SELECT * FROM questions
            WHERE book_id = ?
              AND chapter_id IN ({placeholders})
              AND question_type = ?
            ORDER BY page_start, question_number""",
        [book_id, *chapter_ids, question_type.value],
    ) as cur:
        rows = await cur.fetchall()

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=(
                f"No '{question_type.value}' questions found for topic '{topic}'. "
                f"Run POST /books/{book_id}/chapters/<ch_id>/extract first to populate questions."
            ),
        )

    questions = [row_to_question_record(r) for r in rows]

    # 3. Shuffle or keep in order, then slice to count
    if randomize:
        _random.shuffle(questions)
    selected = questions[:count]

    return GenerateResult(
        questions=selected,
        total=len(selected),
        topic=topic,
        question_type=question_type,
        random=randomize,
    )


# ─────────────────────────────────────────────────────────────────────────────
# POST /api/v1/questions/search  &  GET /api/v1/questions/search
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/api/v1/questions/search",
    response_model=QuestionSearchResponse,
    summary="Multi-facet Question Bank Search",
    description="Search questions by text, subject, class/grade, chapter, question types, difficulty, and marks.",
)
async def search_questions_post(
    query_body: QuestionSearchQuery,
):
    db = await get_db()
    questions, total = await search_questions_db(db, query_body)
    return QuestionSearchResponse(
        questions=questions,
        total=total,
        page=(query_body.offset // query_body.limit) + 1,
        page_size=query_body.limit,
    )


@router.get(
    "/api/v1/questions/search",
    response_model=QuestionSearchResponse,
    summary="Multi-facet Question Bank Search (GET)",
)
async def search_questions_get(
    query: Optional[str] = Query(None, description="Search query string"),
    subject: Optional[str] = Query(None, description="Filter by subject"),
    class_grade: Optional[int] = Query(None, description="Filter by class/grade"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    question_type: Optional[QuestionType] = Query(None, description="Filter by question type"),
    min_marks: Optional[int] = Query(None, description="Minimum marks"),
    max_marks: Optional[int] = Query(None, description="Maximum marks"),
    review_status: Optional[ReviewStatus] = Query(None, description="Filter by review status"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db = await get_db()
    q_types = [question_type] if question_type else None
    diffs = [difficulty] if difficulty else None

    filters = QuestionSearchQuery(
        query=query,
        subject=subject,
        class_grade=class_grade,
        question_types=q_types,
        difficulty=diffs,
        min_marks=min_marks,
        max_marks=max_marks,
        review_status=review_status,
        limit=limit,
        offset=offset,
    )
    questions, total = await search_questions_db(db, filters)
    return QuestionSearchResponse(
        questions=questions,
        total=total,
        page=(offset // limit) + 1,
        page_size=limit,
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/v1/questions/{question_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/api/v1/questions/{question_id}",
    response_model=QuestionRecord,
    summary="Get 3-Layer Question Object",
)
async def get_question_by_id(question_id: str):
    db = await get_db()
    q = await get_question_by_id_db(db, question_id)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
    return q


# ─────────────────────────────────────────────────────────────────────────────
# PATCH /api/v1/questions/{question_id}  (Question Review Studio)
# ─────────────────────────────────────────────────────────────────────────────

@router.patch(
    "/api/v1/questions/{question_id}",
    response_model=QuestionRecord,
    dependencies=[Depends(require_admin)],
    summary="Update/Review Question in Review Studio",
    description="Edit question text, options, difficulty, marks, topic, or approve/reject extraction.",
)
async def patch_question(
    question_id: str,
    patch_data: QuestionPatchRequest,
):
    db = await get_db()
    updated = await update_question_db(db, question_id, patch_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Question not found")
    return updated
