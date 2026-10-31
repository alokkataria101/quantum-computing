"""app/main.py – FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import auth as auth_module
from .auth import User, page_admin, page_user
from .config import settings
from .database import init_db, close_db, get_db
from .routers import books, index, questions, jobs_export, ai, shared, compile as compile_router, assignments, exam_drafts as exam_drafts_router
from .routers import auth as auth_router
from .storage import crops_dir

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
    from .pdf_processor import extract_pdf_meta, extract_pages, run_pdf
    from .chapter_parser import detect_chapters
    from .indexer import upsert_pages, upsert_chapters, rebuild_fts, update_book_status, delete_stale_chapters

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
                meta = await run_pdf(extract_pdf_meta, book_path(book_id))
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
                    sha256, status, created_at)
                   VALUES (?,?,?,?,?,?,?,'pending',?)""",
                (book_id, pdf_path.name, title, author, total_pages,
                 len(data), sha256, now),
            )
            await db.commit()
            logger.info("[autoload] Registered %s → book_id=%s", pdf_path.name, book_id)

            # Index in the background so startup is not blocked
            async def _index(bid: str = book_id, path: Path = book_path(book_id)) -> None:
                try:
                    await update_book_status(bid, "indexing")
                    meta2   = await run_pdf(extract_pdf_meta, path)
                    pages   = await run_pdf(extract_pages, path, ocr_enabled=settings.ocr_enabled,
                                            ocr_language=settings.ocr_language,
                                            dpi=settings.render_dpi)
                    chaps   = await asyncio.to_thread(detect_chapters, bid, meta2, pages)
                    await upsert_chapters(chaps)
                    ch_map  = {pn: ch.chapter_id
                               for ch in chaps
                               for pn in range(ch.page_start, ch.page_end + 1)}
                    await upsert_pages(bid, pages, ch_map)
                    await delete_stale_chapters(bid, [ch.chapter_id for ch in chaps])
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
    crops_dir().mkdir(parents=True, exist_ok=True)
    auth_module.ensure_auth_files()
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

# ── Static files ──────────────────────────────────────────────────────────────
_static_dir = Path(__file__).parent.parent / "static"
_static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")

# Visual Question Crops
_crops_dir = crops_dir()
_crops_dir.mkdir(parents=True, exist_ok=True)
app.mount("/crops", StaticFiles(directory=str(_crops_dir)), name="crops")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth_router.router)
app.include_router(books.router)
app.include_router(index.router)
app.include_router(questions.router)
app.include_router(assignments.router)
app.include_router(exam_drafts_router.router)
app.include_router(jobs_export.router)
app.include_router(ai.router)
app.include_router(shared.router)
app.include_router(compile_router.router)


# ── HTML page viewer ──────────────────────────────────────────────────────────

@app.get("/viewer/{book_id}", response_class=HTMLResponse, include_in_schema=False)
async def viewer(
    request: Request,
    book_id: str,
    page: int = Query(1, ge=1),
    user: User = Depends(page_user),
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


# ── UI — Login / logout ───────────────────────────────────────────────────────

@app.get("/login", response_class=HTMLResponse, include_in_schema=False)
async def login_page(request: Request):
    if auth_module.current_user(request):
        return RedirectResponse("/ui", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html", context={})


# ── UI — Library home page ────────────────────────────────────────────────────

@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def ui_home(request: Request, user: User = Depends(page_user)):
    return templates.TemplateResponse(request=request, name="index.html", context={"user": user})


# ── UI — Assigned tasks (student: mine; admin: everything shared) ─────────────

@app.get("/ui/tasks", response_class=HTMLResponse, include_in_schema=False)
async def ui_tasks(request: Request, user: User = Depends(page_user)):
    return templates.TemplateResponse(request=request, name="tasks.html", context={"user": user})


# ── UI — Student management (admin only) ─────────────────────────────────────

@app.get("/ui/students", response_class=HTMLResponse, include_in_schema=False)
async def ui_students(request: Request, user: User = Depends(page_admin)):
    return templates.TemplateResponse(request=request, name="students.html", context={"user": user})


# ── UI — Compiled PDFs history (admin only) ───────────────────────────────────

@app.get("/ui/compiled-pdfs", response_class=HTMLResponse, include_in_schema=False)
async def ui_compiled_pdfs(request: Request, user: User = Depends(page_admin)):
    return templates.TemplateResponse(request=request, name="compiled_pdfs.html", context={"user": user})


# ── UI — Book detail (chapters list) ─────────────────────────────────────────

@app.get("/ui/books/{book_id}", response_class=HTMLResponse, include_in_schema=False)
async def ui_book(request: Request, book_id: str, user: User = Depends(page_user)):
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
        context={"book": book, "chapters": chapters, "user": user},
    )


# ── UI — Chapter page (reader + questions + AI ask) ───────────────────────────

@app.get("/ui/books/{book_id}/chapters/{chapter_id}", response_class=HTMLResponse, include_in_schema=False)
async def ui_chapter(request: Request, book_id: str, chapter_id: str, user: User = Depends(page_user)):
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
            "user": user,
        },
    )


# ── UI — Question Bank ───────────────────────────────────────────────────────

@app.get("/ui/question-bank", response_class=HTMLResponse, include_in_schema=False)
async def ui_question_bank(
    request: Request,
    book_id: Optional[str] = None,
    question_type: Optional[str] = None,
    difficulty: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(page_user),
):
    from .routers.books import list_books
    from .database import search_questions_db, get_db
    from .models import QuestionSearchQuery, QuestionType, DifficultyLevel

    db = await get_db()
    all_books = await list_books()

    filter_query = QuestionSearchQuery(
        book_ids=[book_id] if book_id else None,
        question_types=[QuestionType(question_type)] if question_type else None,
        difficulties=[DifficultyLevel(difficulty)] if difficulty else None,
        query=q,
        limit=limit,
        offset=offset,
    )
    questions, total = await search_questions_db(db, filter_query)

    return templates.TemplateResponse(
        request=request,
        name="question_bank.html",
        context={
            "user": user,
            "books": all_books,
            "questions": questions,
            "total": total,
            "selected_book_id": book_id or "",
            "question_type": question_type or "",
            "difficulty": difficulty or "",
            "search_query": q or "",
            "limit": limit,
            "offset": offset,
        },
    )


# ── UI — Split-Screen Review Studio ──────────────────────────────────────────

@app.get("/ui/review", response_class=HTMLResponse, include_in_schema=False)
async def ui_review_studio(
    request: Request,
    book_id: Optional[str] = None,
    status: Optional[str] = "pending",
    question_type: Optional[str] = None,
    user: User = Depends(page_user),
):
    from .routers.books import list_books
    from .database import search_questions_db, get_db
    from .models import QuestionSearchQuery, QuestionType, ReviewStatus

    db = await get_db()
    all_books = await list_books()
    status_filter = None if status == "all" else (status or "pending")

    filter_query = QuestionSearchQuery(
        book_ids=[book_id] if book_id else None,
        question_types=[QuestionType(question_type)] if question_type else None,
        review_statuses=[ReviewStatus(status_filter)] if status_filter else None,
        limit=100,
        offset=0,
    )
    questions, total = await search_questions_db(db, filter_query)

    return templates.TemplateResponse(
        request=request,
        name="review_studio.html",
        context={
            "user": user,
            "books": all_books,
            "questions": questions,
            "total": total,
            "selected_book_id": book_id or "",
            "status": status or "pending",
            "question_type": question_type or "",
        },
    )


# ── UI — Assignment Builder ──────────────────────────────────────────────────

@app.get("/ui/assignments", response_class=HTMLResponse, include_in_schema=False)
async def ui_assignments(
    request: Request,
    id: Optional[str] = None,
    user: User = Depends(page_user),
):
    from .routers.books import list_books
    from .database import get_assignment_db, list_assignments_db, get_db

    db = await get_db()
    all_books = await list_books()
    all_assignments, total = await list_assignments_db(db, limit=50)

    active_assignment = None
    if id:
        active_assignment = await get_assignment_db(db, id)
    elif all_assignments:
        active_assignment = await get_assignment_db(db, all_assignments[0].id)

    return templates.TemplateResponse(
        request=request,
        name="assignments.html",
        context={
            "user": user,
            "books": all_books,
            "assignments": all_assignments,
            "active_assignment": active_assignment,
        },
    )


# ── UI — Exam Draft (Exam Paper Builder) ─────────────────────────────────────

@app.get("/ui/exam-draft", response_class=HTMLResponse, include_in_schema=False)
async def ui_exam_draft(
    request: Request,
    draft_id: Optional[str] = None,
    user: User = Depends(page_user),
):
    from .database import get_exam_draft_db, get_or_create_active_draft_db, list_exam_drafts_db

    db = await get_db()
    drafts, _ = await list_exam_drafts_db(db, limit=20)

    active_draft = None
    if draft_id:
        active_draft = await get_exam_draft_db(db, draft_id)
    elif user.is_admin:
        active_draft = await get_or_create_active_draft_db(db, user.username)

    return templates.TemplateResponse(
        request=request,
        name="exam_draft.html",
        context={
            "user": user,
            "drafts": drafts,
            "active_draft": active_draft,
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
        "login": "/login",
        "redoc": "/redoc",
    }


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
