"""app/routers/compile.py – PDF compilation and sharing endpoints.

POST /books/{book_id}/compile-pdf                         admin
    Kick off a background job that compiles a notes PDF, questions PDF,
    or both from the selected chapters of a book.

GET  /books/{book_id}/compile-pdf/{job_id}/download       admin
    Stream the finished PDF back to the browser as a file download.

POST /books/{book_id}/compile-pdf/{job_id}/share          admin
    Share a compiled PDF with all students (or specific ones).

DELETE /shared-pdfs/{share_id}                            admin
    Unshare a compiled PDF.

GET  /shared-pdfs                                         any logged-in user
    List compiled PDFs shared with the caller (students see theirs; admins see all).
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from .. import auth as auth_module
from ..auth import User, require_admin, require_user
from ..config import settings
from ..database import get_db
from ..jobs import create_job, get_job, update_job
from ..models import CompileMode, JobType, SharePdfRequest, SharedPdf, SharedPdfList
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Two sub-routers: one admin-only, one for any logged-in user.
router        = APIRouter(tags=["compile"])
_admin_router = APIRouter(dependencies=[Depends(require_admin)])
_user_router  = APIRouter(dependencies=[Depends(require_user)])

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


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

@_admin_router.post("/books/{book_id}/compile-pdf", response_model=CompileResponse)
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

@_admin_router.get("/books/{book_id}/compile-pdf/{job_id}/download")
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


# ── helpers ───────────────────────────────────────────────────────────────────

async def _pdf_assignees(db, share_ids: list[str]) -> dict[str, list[str]]:
    if not share_ids:
        return {}
    marks = ",".join("?" * len(share_ids))
    out: dict[str, list[str]] = {}
    async with db.execute(
        f"SELECT share_id, student FROM shared_pdf_assignees "
        f"WHERE share_id IN ({marks}) ORDER BY student", share_ids
    ) as cur:
        for r in await cur.fetchall():
            out.setdefault(r["share_id"], []).append(r["student"])
    return out


def _row_to_shared_pdf(r, assigned: dict[str, list[str]], book_title: str | None = None) -> SharedPdf:
    return SharedPdf(
        share_id=r["share_id"],
        book_id=r["book_id"],
        job_id=r["job_id"],
        mode=r["mode"],
        label=r["label"] or "",
        shared_by=r["shared_by"],
        shared_at=datetime.fromisoformat(r["shared_at"]),
        assigned_to=assigned.get(r["share_id"], []),
        book_title=book_title,
    )


_VISIBLE_TO_STUDENT = (
    "(NOT EXISTS (SELECT 1 FROM shared_pdf_assignees a WHERE a.share_id = s.share_id) "
    "OR EXISTS (SELECT 1 FROM shared_pdf_assignees a "
    "WHERE a.share_id = s.share_id AND a.student = ?))"
)


# ── POST /books/{book_id}/compile-pdf/{job_id}/share ─────────────────────────

@_admin_router.post(
    "/books/{book_id}/compile-pdf/{job_id}/share",
    response_model=SharedPdf,
    status_code=status.HTTP_201_CREATED,
)
async def share_compiled_pdf(
    book_id: str,
    job_id: str,
    body: SharePdfRequest,
    admin: User = Depends(require_admin),
):
    job = await get_job(job_id)
    if not job or job["book_id"] != book_id:
        raise HTTPException(status_code=404, detail="Job not found.")
    if job["status"] != "done":
        raise HTTPException(status_code=409, detail="PDF is not ready yet.")

    # Find the compiled file to confirm it exists
    found: Path | None = None
    for mode in CompileMode:
        p = _export_path(book_id, job_id, mode)
        if p.exists():
            found = p
            break
    if not found:
        raise HTTPException(status_code=404, detail="Compiled PDF file not found on disk.")

    targets: list[str] = []
    if body.students:
        known = set(auth_module.list_students())
        targets = sorted(set(body.students))
        unknown = [s for s in targets if s not in known]
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown student(s): {', '.join(unknown)}")

    db = await get_db()
    async with db.execute("SELECT title FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    book_title = brow["title"] if brow else ""

    # Detect mode from filename
    mode_val = found.stem.split("_")[-1]

    share_id = str(uuid.uuid4())
    label    = body.label or f"{book_title} — {mode_val}"
    await db.execute(
        "INSERT INTO shared_pdfs (share_id, book_id, job_id, mode, label, shared_by, shared_at) "
        "VALUES (?,?,?,?,?,?,?)",
        (share_id, book_id, job_id, mode_val, label, admin.username, _now()),
    )
    for student in targets:
        await db.execute(
            "INSERT INTO shared_pdf_assignees (share_id, student) VALUES (?,?)",
            (share_id, student),
        )
    await db.commit()

    async with db.execute("SELECT * FROM shared_pdfs WHERE share_id = ?", (share_id,)) as cur:
        row = await cur.fetchone()
    assigned = await _pdf_assignees(db, [share_id])
    return _row_to_shared_pdf(row, assigned, book_title)


# ── DELETE /shared-pdfs/{share_id} ───────────────────────────────────────────

@_admin_router.delete("/shared-pdfs/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_pdf(share_id: str):
    db = await get_db()
    cur = await db.execute("DELETE FROM shared_pdfs WHERE share_id = ?", (share_id,))
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Shared PDF not found.")


# ── GET /shared-pdfs ─────────────────────────────────────────────────────────

@_user_router.get("/shared-pdfs", response_model=SharedPdfList)
async def list_shared_pdfs(user: User = Depends(require_user)):
    """List compiled PDFs shared with the caller. Students see theirs; admins see all."""
    db = await get_db()
    if user.is_admin:
        sql    = "SELECT s.*, b.title AS book_title FROM shared_pdfs s LEFT JOIN books b ON b.book_id = s.book_id ORDER BY s.shared_at DESC"
        params: list = []
    else:
        sql    = (
            "SELECT s.*, b.title AS book_title FROM shared_pdfs s "
            "LEFT JOIN books b ON b.book_id = s.book_id "
            f"WHERE {_VISIBLE_TO_STUDENT} ORDER BY s.shared_at DESC"
        )
        params = [user.username]
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()
    assigned = await _pdf_assignees(db, [r["share_id"] for r in rows])
    pdfs = [_row_to_shared_pdf(r, assigned, r["book_title"]) for r in rows]
    return SharedPdfList(pdfs=pdfs, total=len(pdfs))


# ── GET /shared-pdfs/{share_id}/download ─────────────────────────────────────

@_user_router.get("/shared-pdfs/{share_id}/download")
async def download_shared_pdf(share_id: str, user: User = Depends(require_user)):
    """Download a shared compiled PDF. Students can only download ones shared with them."""
    db = await get_db()
    async with db.execute("SELECT * FROM shared_pdfs WHERE share_id = ?", (share_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Shared PDF not found.")

    # Access check for students
    if not user.is_admin:
        assigned = await _pdf_assignees(db, [share_id])
        targets  = assigned.get(share_id, [])
        if targets and user.username not in targets:
            raise HTTPException(status_code=403, detail="This PDF was not shared with you.")

    found: Path | None = None
    for mode in CompileMode:
        p = _export_path(row["book_id"], row["job_id"], mode)
        if p.exists():
            found = p
            break
    if not found:
        raise HTTPException(status_code=404, detail="PDF file not found on disk.")

    safe_label = (row["label"] or row["share_id"]).replace(" ", "_")[:60]
    filename   = f"{safe_label}.pdf"
    return FileResponse(
        path=str(found),
        media_type="application/pdf",
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── wire sub-routers into the main router ────────────────────────────────────
router.include_router(_admin_router)
router.include_router(_user_router)
