"""app/main.py – FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .config import settings
from .database import init_db, close_db, get_db
from .routers import books, index, questions, jobs_export, ai

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# Intake folder: book-knowledge-service/books/
# Drop PDFs here before starting the server — they are auto-registered and indexed.
_INTAKE_DIR = Path(__file__).resolve().parent.parent / "books"


async def _autoload_intake_books() -> None:
    """Register and index any PDFs found in the intake folder at startup."""
    _INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    pdfs = sorted(_INTAKE_DIR.glob("*.pdf"))
    if not pdfs:
        return

    from .database import get_db as _get_db
    from .storage import save_uploaded_pdf, compute_sha256, book_path
    from .pdf_processor import extract_pdf_meta, extract_pages
    from .chapter_parser import detect_chapters
    from .indexer import upsert_pages, upsert_chapters, rebuild_fts, update_book_status

    db = await _get_db()

    for pdf_path in pdfs:
        try:
            data = pdf_path.read_bytes()
            sha256 = compute_sha256(data)

            # Skip if already registered
            async with db.execute("SELECT book_id FROM books WHERE sha256 = ?", (sha256,)) as cur:
                existing = await cur.fetchone()
            if existing:
                logger.info("[autoload] %s already registered (book_id=%s), skipping.", pdf_path.name, existing["book_id"])
                continue

            book_id = str(uuid.uuid4())
            await save_uploaded_pdf(data, book_id)

            try:
                meta = extract_pdf_meta(book_path(book_id))
                title       = meta.title or pdf_path.stem
                author      = meta.author or ""
                total_pages = meta.total_pages
            except Exception:
                title, author, total_pages = pdf_path.stem, "", 0

            from datetime import datetime, timezone
            now = datetime.now(timezone.utc).isoformat()
            await db.execute(
                """INSERT INTO books
                   (book_id, filename, title, author, total_pages, file_size,
                    sha256, status, uploaded_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,'pending',?,?)""",
                (book_id, pdf_path.name, title, author, total_pages,
                 len(data), sha256, now, now),
            )
            await db.commit()
            logger.info("[autoload] Registered %s → book_id=%s", pdf_path.name, book_id)

            # Index in the background so startup is not blocked
            async def _index(bid: str = book_id, path: Path = book_path(book_id)) -> None:
                try:
                    await update_book_status(bid, "indexing")
                    meta2   = extract_pdf_meta(path)
                    pages   = extract_pages(path, ocr_enabled=settings.ocr_enabled,
                                            ocr_language=settings.ocr_language,
                                            dpi=settings.render_dpi)
                    chaps   = detect_chapters(bid, meta2, pages)
                    await upsert_chapters(chaps)
                    ch_map  = {pn: ch.chapter_id
                               for ch in chaps
                               for pn in range(ch.page_start, ch.page_end + 1)}
                    await upsert_pages(bid, pages, ch_map)
                    await rebuild_fts(bid)
                    await update_book_status(bid, "indexed",
                                             total_pages=len(pages),
                                             title=meta2.title or None,
                                             author=meta2.author or None)
                    logger.info("[autoload] Indexed %s (%d pages).", path.name, len(pages))
                except Exception as exc:
                    await update_book_status(bid, "error", error=str(exc))
                    logger.error("[autoload] Failed to index %s: %s", path.name, exc)

            asyncio.create_task(_index())

        except Exception as exc:
            logger.error("[autoload] Error processing %s: %s", pdf_path.name, exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.books_dir.mkdir(parents=True, exist_ok=True)
    settings.indexes_dir.mkdir(parents=True, exist_ok=True)
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    await init_db()
    await _autoload_intake_books()
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
templates.env.auto_reload = True  # re-read templates from disk on every request (no restart needed)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(books.router)
app.include_router(index.router)
app.include_router(questions.router)
app.include_router(jobs_export.router)
app.include_router(ai.router)


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


# ── UI — Library home page ────────────────────────────────────────────────────

@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def ui_home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


# ── UI — Book detail (chapters list) ─────────────────────────────────────────

@app.get("/ui/books/{book_id}", response_class=HTMLResponse, include_in_schema=False)
async def ui_book(request: Request, book_id: str):
    db = await get_db()

    async with db.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    if not brow:
        raise HTTPException(status_code=404, detail="Book not found.")

    async with db.execute(
        "SELECT * FROM chapters WHERE book_id = ? ORDER BY number", (book_id,)
    ) as cur:
        ch_rows = await cur.fetchall()

    from .routers.books import _row_to_book
    from .models import ChapterRecord

    book = _row_to_book(brow)
    chapters = [
        ChapterRecord(
            chapter_id=r["chapter_id"], book_id=r["book_id"],
            number=r["number"], title=r["title"],
            page_start=r["page_start"], page_end=r["page_end"],
            confidence=r["confidence"], source=r["source"],
        )
        for r in ch_rows
    ]

    return templates.TemplateResponse(
        request=request, name="book.html",
        context={"book": book, "chapters": chapters},
    )


# ── UI — Chapter page (reader + questions + AI ask) ───────────────────────────

@app.get("/ui/books/{book_id}/chapters/{chapter_id}", response_class=HTMLResponse, include_in_schema=False)
async def ui_chapter(request: Request, book_id: str, chapter_id: str):
    db = await get_db()

    async with db.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)) as cur:
        brow = await cur.fetchone()
    if not brow:
        raise HTTPException(status_code=404, detail="Book not found.")

    async with db.execute(
        "SELECT * FROM chapters WHERE chapter_id = ? AND book_id = ?", (chapter_id, book_id)
    ) as cur:
        crow = await cur.fetchone()
    if not crow:
        raise HTTPException(status_code=404, detail="Chapter not found.")

    async with db.execute(
        "SELECT * FROM chapters WHERE book_id = ? ORDER BY number", (book_id,)
    ) as cur:
        all_ch = await cur.fetchall()

    from .routers.books import _row_to_book
    from .models import ChapterRecord

    book = _row_to_book(brow)

    def to_ch(r):
        return ChapterRecord(
            chapter_id=r["chapter_id"], book_id=r["book_id"],
            number=r["number"], title=r["title"],
            page_start=r["page_start"], page_end=r["page_end"],
            confidence=r["confidence"], source=r["source"],
        )

    chapter    = to_ch(crow)
    chapters   = [to_ch(r) for r in all_ch]
    idx        = next((i for i, c in enumerate(chapters) if c.chapter_id == chapter_id), None)
    prev_chapter = chapters[idx - 1] if idx and idx > 0 else None
    next_chapter = chapters[idx + 1] if idx is not None and idx < len(chapters) - 1 else None

    return templates.TemplateResponse(
        request=request, name="chapter.html",
        context={
            "book": book,
            "chapter": chapter,
            "prev_chapter": prev_chapter,
            "next_chapter": next_chapter,
        },
    )


# ── Root / health ─────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "book-knowledge-service",
        "version": "1.0.0",
        "docs": "/docs",
        "ui": "/ui",
        "redoc": "/redoc",
    }


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
