"""app/routers/books.py – POST /books, GET /books, GET /books/{book_id}"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from ..config import settings
from ..database import get_db
from ..models import BookRecord, BookList, BookStatus
from ..storage import save_uploaded_pdf, validate_pdf_bytes, compute_sha256
from ..pdf_processor import extract_pdf_meta

router = APIRouter(prefix="/books", tags=["books"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("", status_code=status.HTTP_201_CREATED, response_model=BookRecord)
async def upload_book(file: UploadFile = File(...)):
    """Upload a PDF and register it as a book."""
    data = await file.read()

    # Validate
    try:
        validate_pdf_bytes(data, settings.max_upload_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sha256 = compute_sha256(data)
    db = await get_db()

    # Deduplication check
    async with db.execute("SELECT book_id FROM books WHERE sha256 = ?", (sha256,)) as cur:
        existing = await cur.fetchone()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Book already registered with id={existing['book_id']}.",
        )

    book_id = str(uuid.uuid4())
    _, file_size = await save_uploaded_pdf(data, book_id)

    # Best-effort metadata extraction
    from ..storage import book_path
    try:
        meta = extract_pdf_meta(book_path(book_id))
        title  = meta.title or file.filename or "Unknown"
        author = meta.author or ""
        total_pages = meta.total_pages
    except Exception:
        title, author, total_pages = file.filename or "Unknown", "", 0

    now = _now()
    await db.execute(
        """INSERT INTO books (book_id, filename, title, author, sha256, file_size,
                              total_pages, status, created_at)
           VALUES (?,?,?,?,?,?,?,'uploaded',?)""",
        (book_id, file.filename or "", title, author, sha256, file_size, total_pages, now),
    )
    await db.commit()

    return BookRecord(
        book_id=book_id, filename=file.filename or "", title=title,
        author=author, sha256=sha256, file_size=file_size,
        total_pages=total_pages, status=BookStatus.uploaded,
        created_at=datetime.fromisoformat(now),
    )


@router.get("", response_model=BookList)
async def list_books():
    db = await get_db()
    async with db.execute("SELECT * FROM books ORDER BY created_at DESC") as cur:
        rows = await cur.fetchall()
    books = [_row_to_book(r) for r in rows]
    return BookList(books=books, total=len(books))


@router.get("/{book_id}", response_model=BookRecord)
async def get_book(book_id: str):
    db = await get_db()
    async with db.execute("SELECT * FROM books WHERE book_id = ?", (book_id,)) as cur:
        row = await cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Book not found.")
    return _row_to_book(row)


def _row_to_book(row) -> BookRecord:
    d = dict(row)
    return BookRecord(
        book_id=d["book_id"],
        filename=d["filename"],
        title=d["title"],
        author=d["author"],
        sha256=d["sha256"],
        file_size=d["file_size"],
        total_pages=d["total_pages"],
        status=BookStatus(d["status"]),
        created_at=datetime.fromisoformat(d["created_at"]),
        indexed_at=datetime.fromisoformat(d["indexed_at"]) if d.get("indexed_at") else None,
        error_message=d.get("error_message"),
    )
