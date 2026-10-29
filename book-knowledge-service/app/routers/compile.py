"""app/routers/compile.py – admin-only PDF compilation endpoints.

POST /books/{book_id}/compile-pdf
    Kick off a background job that compiles a notes PDF, questions PDF,
    or both from the selected chapters of a book.

GET  /books/{book_id}/compile-pdf/{job_id}/download
    Stream the finished PDF back to the browser as a file download.
    Only the job owner (same session) or any admin can download.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..auth import User, require_admin
from ..config import settings
from ..database import get_db
from ..jobs import create_job, get_job, run_job, update_job
from ..models import CompileMode, JobType

logger = logging.getLogger(__name__)

router = APIRouter(tags=["compile"], dependencies=[Depends(require_admin)])


# ── request / response schemas ────────────────────────────────────────────────

class CompileRequest(BaseModel):
    mode: CompileMode = CompileMode.questions
    chapter_ids: list[str] = Field(
        default_factory=list,
        description="Chapter IDs to include. Empty list = all chapters.",
    )
    dpi: int = Field(170, ge=72, le=300, description="Render DPI (quality vs speed).")


class CompileResponse(BaseModel):
    job_id: str
    message: str


# ── helpers ───────────────────────────────────────────────────────────────────

def _export_path(book_id: str, job_id: str, mode: CompileMode) -> Path:
    return settings.exports_dir / f"{book_id}_{job_id}_{mode.value}.pdf"


# ── POST /books/{book_id}/compile-pdf ─────────────────────────────────────────

@router.post("/books/{book_id}/compile-pdf", response_model=CompileResponse)
async def start_compile(book_id: str, req: CompileRequest):
    db = await get_db()

    # Verify book exists and is indexed
    async with db.execute(
        "SELECT title, status FROM books WHERE book_id = ?", (book_id,)
    ) as cur:
        brow = await cur.fetchone()
    if not brow:
        raise HTTPException(status_code=404, detail="Book not found.")
    if brow["status"] not in ("indexed",):
        raise HTTPException(
            status_code=409,
            detail=f"Book is not indexed yet (status: {brow['status']}). Index it first.",
        )

    book_title = brow["title"] or book_id

    # Fetch selected chapters (or all)
    if req.chapter_ids:
        placeholders = ",".join("?" * len(req.chapter_ids))
        async with db.execute(
            f"SELECT * FROM chapters WHERE book_id = ? AND chapter_id IN ({placeholders}) ORDER BY number",
            [book_id, *req.chapter_ids],
        ) as cur:
            ch_rows = [dict(r) for r in await cur.fetchall()]
    else:
        async with db.execute(
            "SELECT * FROM chapters WHERE book_id = ? ORDER BY number", (book_id,)
        ) as cur:
            ch_rows = [dict(r) for r in await cur.fetchall()]

    if not ch_rows:
        raise HTTPException(status_code=404, detail="No matching chapters found.")

    job_id   = await create_job(JobType.compile_pdf.value, book_id)
    out_path = _export_path(book_id, job_id, req.mode)

    async def _run():
        from ..compiler import compile_pdf

        loop = asyncio.get_event_loop()

        def _progress(msg: str):
            # Called from a worker thread — schedule the coroutine on the
            # event loop that owns this async task.
            asyncio.run_coroutine_threadsafe(update_job(job_id, message=msg), loop)

        try:
            await asyncio.to_thread(
                compile_pdf,
                book_id,
                ch_rows,
                req.mode,
                out_path,
                book_title,
                _progress,
                req.dpi,
            )
            pages = 0
            if out_path.exists():
                import pymupdf as fitz
                doc = fitz.open(out_path)
                pages = doc.page_count
                doc.close()
            await update_job(
                job_id,
                status="done",
                progress=1.0,
                message=f"PDF ready ({pages} pages). "
                        f"job_id={job_id} mode={req.mode.value}",
            )
        except Exception as exc:
            logger.exception("compile_pdf job %s failed", job_id)
            await update_job(job_id, status="failed", error=str(exc),
                             message="Compilation failed.")
            raise

    asyncio.create_task(_run())
    await update_job(job_id, status="running", progress=0.05,
                     message="Compilation started…")

    return CompileResponse(
        job_id=job_id,
        message=f"Compilation job {job_id} started.",
    )


# ── GET /books/{book_id}/compile-pdf/{job_id}/download ───────────────────────

@router.get("/books/{book_id}/compile-pdf/{job_id}/download")
async def download_compiled(book_id: str, job_id: str):
    job = await get_job(job_id)
    if not job or job["book_id"] != book_id:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"Job is not complete yet (status: {job['status']}).",
        )

    # Find the file — we may not know the exact mode from the job record,
    # so try all three modes.
    found: Path | None = None
    for mode in CompileMode:
        p = _export_path(book_id, job_id, mode)
        if p.exists():
            found = p
            break

    if not found:
        raise HTTPException(status_code=404, detail="Output file not found on disk.")

    db = await get_db()
    async with db.execute("SELECT title FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    safe_title = (brow["title"] if brow else book_id).replace(" ", "_")[:40]
    filename   = f"{safe_title}_{found.stem.split('_')[-1]}.pdf"

    return FileResponse(
        path=str(found),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
