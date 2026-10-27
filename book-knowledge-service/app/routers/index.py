"""app/routers/index.py – POST /books/{id}/index, GET /books/{id}/chapters,
                          GET /books/{id}/pages/{n}, GET /books/{id}/pages/{n}/render,
                          GET /books/{id}/search"""

from __future__ import annotations

import asyncio
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from ..auth import require_admin, require_user
from ..config import settings
from ..database import get_db
from ..indexer import (
    upsert_pages, upsert_chapters, rebuild_fts,
    update_book_status, full_text_search,
)
from ..chapter_parser import detect_chapters
from ..jobs import create_job, run_job, update_job
from ..models import ChapterList, ChapterRecord, PageRecord, JobRecord, JobStatus, JobType, SearchResult, SearchHit
from ..pdf_processor import extract_pages, extract_pdf_meta, render_page_to_png, render_page_figures
from ..storage import book_path, rendered_page_path

router = APIRouter(tags=["indexing"], dependencies=[Depends(require_user)])


# ─────────────────────────────────────────────────────────────────────────────
# POST /books/{book_id}/index  – start indexing job
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/books/{book_id}/index", response_model=JobRecord,
             dependencies=[Depends(require_admin)])
async def start_index(book_id: str):
    db = await get_db()
    async with db.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Book not found.")

    job_id = await create_job(JobType.index, book_id)

    async def _do_index():
        path = book_path(book_id)
        if not path.exists():
            raise FileNotFoundError(f"PDF file missing for book {book_id}.")

        await update_book_status(book_id, "indexing")
        await update_job(job_id, progress=0.05, message="Extracting PDF metadata…")

        meta = extract_pdf_meta(path)
        await update_job(job_id, progress=0.1, message="Extracting page text…")

        pages = extract_pages(
            path,
            ocr_enabled=settings.ocr_enabled,
            ocr_language=settings.ocr_language,
            dpi=settings.render_dpi,
        )
        await update_job(job_id, progress=0.6, message="Detecting chapters…")

        chapters = detect_chapters(book_id, meta, pages)
        await upsert_chapters(chapters)

        # Build page → chapter map
        chapter_map: dict[int, str] = {}
        for ch in chapters:
            for pn in range(ch.page_start, ch.page_end + 1):
                chapter_map[pn] = ch.chapter_id

        await update_job(job_id, progress=0.7, message="Saving pages…")
        await upsert_pages(book_id, pages, chapter_map)

        await update_job(job_id, progress=0.9, message="Building FTS index…")
        await rebuild_fts(book_id)

        await update_book_status(
            book_id, "indexed",
            total_pages=len(pages),
            title=meta.title or None,
            author=meta.author or None,
        )
        await update_job(job_id, progress=1.0, status="done", message="Indexing complete.")

    asyncio.create_task(_do_index())

    return JobRecord(
        job_id=job_id, job_type=JobType.index, book_id=book_id,
        status=JobStatus.pending, progress=0.0,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/chapters
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/books/{book_id}/chapters", response_model=ChapterList)
async def list_chapters(book_id: str):
    db = await get_db()
    async with db.execute(
        "SELECT * FROM chapters WHERE book_id = ? ORDER BY number", (book_id,)
    ) as cur:
        rows = await cur.fetchall()
    if not rows:
        raise HTTPException(status_code=404, detail="No chapters found. Run /index first.")
    chapters = [
        ChapterRecord(
            chapter_id=r["chapter_id"], book_id=r["book_id"],
            number=r["number"], title=r["title"],
            page_start=r["page_start"], page_end=r["page_end"],
            confidence=r["confidence"], source=r["source"],
        )
        for r in rows
    ]
    return ChapterList(chapters=chapters)


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/pages/{page_number}
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/books/{book_id}/pages/{page_number}", response_model=PageRecord)
async def get_page(book_id: str, page_number: int):
    db = await get_db()
    async with db.execute(
        "SELECT * FROM pages WHERE book_id = ? AND page_number = ?",
        (book_id, page_number),
    ) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Page {page_number} not found.")
    return PageRecord(
        book_id=row["book_id"], page_number=row["page_number"],
        text=row["text"], has_images=bool(row["has_images"]),
        is_scanned=bool(row["is_scanned"]), ocr_used=bool(row["ocr_used"]),
        chapter_id=row["chapter_id"],
    )


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/pages/{page_number}/render  – PNG image
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/books/{book_id}/pages/{page_number}/render")
async def render_page(book_id: str, page_number: int, dpi: int = Query(150, ge=72, le=300)):
    cached = rendered_page_path(book_id, page_number)
    if cached.exists():
        return Response(cached.read_bytes(), media_type="image/png")
    path = book_path(book_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    try:
        png = render_page_to_png(path, page_number, dpi=dpi)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    cached.write_bytes(png)
    return Response(png, media_type="image/png")


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/pages/{page_number}/render/figures  – cropped figure PNG
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/books/{book_id}/pages/{page_number}/render/figures")
async def render_page_figures_endpoint(
    book_id: str,
    page_number: int,
    dpi: int = Query(150, ge=72, le=300),
):
    """Return a PNG cropped to only the image/figure regions on the page.
    Falls back to the full-page render if no figures are detected."""
    path = book_path(book_id)
    if not path.exists():
        raise HTTPException(status_code=404, detail="PDF file not found.")
    try:
        png = render_page_figures(path, page_number, dpi=dpi)
        if png is None:
            # No figures on this page — fall back to full-page render
            cached = rendered_page_path(book_id, page_number)
            if cached.exists():
                png = cached.read_bytes()
            else:
                png = render_page_to_png(path, page_number, dpi=dpi)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return Response(png, media_type="image/png")


# ─────────────────────────────────────────────────────────────────────────────
# GET /books/{book_id}/search?q=...
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/books/{book_id}/search", response_model=SearchResult)
async def search_book(
    book_id: str,
    q: str = Query(..., min_length=1),
    chapter_id: str | None = None,
    limit: int = Query(20, ge=1, le=100),
):
    hits_raw = await full_text_search(q, book_id=book_id, chapter_id=chapter_id, limit=limit)
    hits = [
        SearchHit(
            book_id=h["book_id"], page_number=h["page_number"],
            chapter_id=h["chapter_id"], snippet=h["snippet"],
            score=float(h.get("rank", 0.0)) * -1,
        )
        for h in hits_raw
    ]
    return SearchResult(hits=hits, total=len(hits), query=q)
