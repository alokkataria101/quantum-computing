"""app/main.py – FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import init_db, close_db, get_db
from .routers import books, index, questions, jobs_export

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.books_dir.mkdir(parents=True, exist_ok=True)
    settings.indexes_dir.mkdir(parents=True, exist_ok=True)
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    logger.info("book-knowledge-service started.")
    yield
    await close_db()
    logger.info("book-knowledge-service stopped.")


app = FastAPI(
    title="Book Knowledge Service",
    description=(
        "Upload PDF textbooks, index them, view pages, extract chapters, "
        "and export questions and examples."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(books.router)
app.include_router(index.router)
app.include_router(questions.router)
app.include_router(jobs_export.router)


# ── HTML page viewer ──────────────────────────────────────────────────────────

@app.get("/viewer/{book_id}", response_class=HTMLResponse, include_in_schema=False)
async def viewer(
    request: Request,
    book_id: str,
    page: int = Query(1, ge=1),
):
    db = await get_db()

    async with db.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    if not brow:
        raise HTTPException(status_code=404, detail="Book not found.")

    # Clamp page
    total = brow["total_pages"] or 1
    page = max(1, min(page, total))

    # Get page text
    async with db.execute(
        "SELECT text, is_scanned, ocr_used, chapter_id FROM pages WHERE book_id=? AND page_number=?",
        (book_id, page),
    ) as cur:
        prow = await cur.fetchone()
    page_text    = prow["text"] if prow else "(Page not yet indexed)"
    page_scanned = bool(prow["is_scanned"]) if prow else False
    page_ocr     = bool(prow["ocr_used"])   if prow else False
    chapter_id   = prow["chapter_id"]       if prow else None

    # Get chapters for sidebar
    async with db.execute(
        "SELECT * FROM chapters WHERE book_id=? ORDER BY number", (book_id,)
    ) as cur:
        ch_rows = await cur.fetchall()

    from .models import ChapterRecord
    chapters = [
        ChapterRecord(
            chapter_id=r["chapter_id"], book_id=r["book_id"],
            number=r["number"], title=r["title"],
            page_start=r["page_start"], page_end=r["page_end"],
            confidence=r["confidence"], source=r["source"],
        )
        for r in ch_rows
    ]

    # Identify current chapter title
    current_chapter_title = ""
    current_chapter_num   = 0
    for ch in chapters:
        if ch.chapter_id == chapter_id:
            current_chapter_title = ch.title
            current_chapter_num   = ch.number
            break

    from .routers.books import _row_to_book
    book = _row_to_book(brow)

    return templates.TemplateResponse(
        request=request,
        name="viewer.html",
        context={
            "book": book,
            "chapters": chapters,
            "current_page": page,
            "current_chapter": current_chapter_num,
            "current_chapter_title": current_chapter_title,
            "page_text": page_text,
            "page_scanned": page_scanned,
            "page_ocr": page_ocr,
        },
    )


# ── Root / health ─────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "book-knowledge-service",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
