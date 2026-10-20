"""app/indexer.py – persist extracted pages and rebuild FTS5 full-text index."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

import aiosqlite

from .database import get_db
from .models import ChapterRecord, PageRecord
from .pdf_processor import ExtractedPage

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def upsert_pages(
    book_id: str,
    pages: list[ExtractedPage],
    chapter_map: dict[int, str],   # page_number → chapter_id
) -> None:
    """Insert or replace all extracted pages for a book."""
    db = await get_db()
    rows = [
        (
            book_id,
            ep.page_number,
            ep.text,
            int(ep.has_images),
            int(ep.is_scanned),
            int(ep.ocr_used),
            chapter_map.get(ep.page_number),
        )
        for ep in pages
    ]
    await db.executemany(
        """INSERT OR REPLACE INTO pages
           (book_id, page_number, text, has_images, is_scanned, ocr_used, chapter_id)
           VALUES (?,?,?,?,?,?,?)""",
        rows,
    )
    await db.commit()
    logger.info("Upserted %d pages for book %s", len(rows), book_id)


async def upsert_chapters(chapters: list[ChapterRecord]) -> None:
    db = await get_db()
    rows = [
        (
            ch.chapter_id, ch.book_id, ch.number, ch.title,
            ch.page_start, ch.page_end, ch.confidence, ch.source,
        )
        for ch in chapters
    ]
    await db.executemany(
        """INSERT OR REPLACE INTO chapters
           (chapter_id, book_id, number, title, page_start, page_end, confidence, source)
           VALUES (?,?,?,?,?,?,?,?)""",
        rows,
    )
    await db.commit()


async def rebuild_fts(book_id: str) -> None:
    """
    Repopulate the FTS5 virtual table for all pages of a book.
    Deletes existing FTS entries for this book first.

    FTS5 virtual tables do not support WHERE on non-indexed columns directly.
    We delete by rowid (= page_id) obtained from the pages table.
    """
    db = await get_db()

    # Collect rowids belonging to this book from the real pages table
    async with db.execute(
        "SELECT page_id FROM pages WHERE book_id = ?", (book_id,)
    ) as cur:
        rowid_rows = await cur.fetchall()

    # Delete each FTS row by rowid
    for r in rowid_rows:
        await db.execute("DELETE FROM pages_fts WHERE rowid = ?", (r["page_id"],))

    # Reinsert via rowid sync
    await db.execute("""
        INSERT INTO pages_fts(rowid, text, book_id, page_number, chapter_id)
        SELECT page_id, text, book_id, page_number, chapter_id
        FROM pages WHERE book_id = ?
    """, (book_id,))
    await db.commit()
    logger.info("FTS index rebuilt for book %s", book_id)


async def update_book_status(
    book_id: str,
    status: str,
    total_pages: int | None = None,
    title: str | None = None,
    author: str | None = None,
    error: str | None = None,
) -> None:
    db = await get_db()
    fields: list[str] = ["status = ?"]
    params: list = [status]
    if total_pages is not None:
        fields.append("total_pages = ?"); params.append(total_pages)
    if title is not None:
        fields.append("title = ?"); params.append(title)
    if author is not None:
        fields.append("author = ?"); params.append(author)
    if error is not None:
        fields.append("error_message = ?"); params.append(error)
    if status == "indexed":
        fields.append("indexed_at = ?"); params.append(_now())
    params.append(book_id)
    await db.execute(f"UPDATE books SET {', '.join(fields)} WHERE book_id = ?", params)
    await db.commit()


async def full_text_search(
    query: str,
    book_id: str | None = None,
    chapter_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Run a FTS5 query and return ranked hits with snippets."""
    db = await get_db()
    where_clauses: list[str] = ["pages_fts MATCH ?"]
    params: list = [query]
    if book_id:
        where_clauses.append("book_id = ?"); params.append(book_id)
    if chapter_id:
        where_clauses.append("chapter_id = ?"); params.append(chapter_id)
    params.append(limit)

    sql = f"""
        SELECT book_id, page_number, chapter_id,
               snippet(pages_fts, 0, '<b>', '</b>', '…', 32) AS snippet,
               rank
        FROM pages_fts
        WHERE {' AND '.join(where_clauses)}
        ORDER BY rank
        LIMIT ?
    """
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]
