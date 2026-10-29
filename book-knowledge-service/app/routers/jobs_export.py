"""app/routers/jobs_export.py – GET /jobs/{job_id}, GET /books/{id}/export"""

from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from ..auth import require_user
from ..database import get_db
from ..exporter import export
from ..jobs import get_job
from ..models import ExportFormat, ExportRequest, JobRecord, JobStatus, JobType, QuestionType

router = APIRouter(tags=["jobs", "export"], dependencies=[Depends(require_user)])


# ─────────────────────────────────────────────────────────────────────────────
# GET /jobs/{job_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobRecord)
async def check_job(job_id: str):
    from datetime import datetime
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return JobRecord(
        job_id=job["job_id"],
        job_type=JobType(job["job_type"]),
        book_id=job["book_id"],
        chapter_id=job.get("chapter_id"),
        status=JobStatus(job["status"]),
        progress=job["progress"],
        message=job.get("message", ""),
        error=job.get("error"),
        created_at=datetime.fromisoformat(job["created_at"]),
        updated_at=datetime.fromisoformat(job["updated_at"]),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/export
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/books/{book_id}/export")
async def export_book(
    book_id: str,
    fmt: ExportFormat = Query(ExportFormat.json),
    chapter_ids: str | None = Query(None, description="Comma-separated chapter IDs"),
    question_types: str | None = Query(None, description="Comma-separated question types"),
    include_solutions: bool = Query(True),
):
    db = await get_db()

    # Get book
    async with db.execute("SELECT title FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    if not brow:
        raise HTTPException(status_code=404, detail="Book not found.")
    book_title = brow["title"]

    # Get chapters
    ch_filter = ""
    ch_params: list = [book_id]
    if chapter_ids:
        ids = [c.strip() for c in chapter_ids.split(",")]
        placeholders = ",".join("?" * len(ids))
        ch_filter = f" AND chapter_id IN ({placeholders})"
        ch_params += ids

    async with db.execute(
        f"SELECT * FROM chapters WHERE book_id = ?{ch_filter} ORDER BY number",
        ch_params,
    ) as cur:
        ch_rows = await cur.fetchall()

    from ..models import ChapterRecord
    chapters = [
        ChapterRecord(
            chapter_id=r["chapter_id"], book_id=r["book_id"],
            number=r["number"], title=r["title"],
            page_start=r["page_start"], page_end=r["page_end"],
            confidence=r["confidence"], source=r["source"],
        )
        for r in ch_rows
    ]

    # Get questions
    q_where = "book_id = ?"
    q_params: list = [book_id]
    if chapter_ids:
        ids = [c.strip() for c in chapter_ids.split(",")]
        placeholders = ",".join("?" * len(ids))
        q_where += f" AND chapter_id IN ({placeholders})"
        q_params += ids
    if question_types:
        types = [t.strip() for t in question_types.split(",")]
        placeholders = ",".join("?" * len(types))
        q_where += f" AND question_type IN ({placeholders})"
        q_params += types

    async with db.execute(
        f"SELECT * FROM questions WHERE {q_where} ORDER BY chapter_number, page_start",
        q_params,
    ) as cur:
        q_rows = await cur.fetchall()

    from ..routers.questions import _row_to_q
    questions = [_row_to_q(r) for r in q_rows]

    if not questions:
        raise HTTPException(status_code=404, detail="No questions found matching the filters.")

    try:
        # PDF/HTML building is pure-Python CPU work; keep it off the event loop.
        content, media_type = await asyncio.to_thread(
            export, fmt, questions, chapters, book_title, include_solutions)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))

    ext_map = {
        ExportFormat.json: "json", ExportFormat.csv: "csv",
        ExportFormat.html: "html", ExportFormat.pdf: "pdf",
    }
    filename = f"{book_id}_questions.{ext_map[fmt]}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
