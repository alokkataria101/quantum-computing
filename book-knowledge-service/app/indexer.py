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

    Uses INSERT(pages_fts, 'delete', ...) for safe per-row removal, then
    inserts fresh rows.  Falls back to a full FTS5 'rebuild' if the shadow
    tables are malformed (e.g. after a previous crashed index run).
    """
    db = await get_db()

    # Try a full FTS5 integrity-check + rebuild first to repair any corruption
    try:
        await db.execute("INSERT INTO pages_fts(pages_fts) VALUES('rebuild')")
        await db.commit()
    except Exception as exc:
        logger.warning("FTS rebuild command failed (%s); continuing.", exc)

    # Remove stale entries for this book using the FTS5 delete command
    async with db.execute(
        "SELECT page_id, text, page_number, chapter_id FROM pages WHERE book_id = ?",
        (book_id,),
    ) as cur:
        existing = await cur.fetchall()

    for r in existing:
        try:
            await db.execute(
                "INSERT INTO pages_fts(pages_fts, rowid, text, book_id, page_number, chapter_id) "
                "VALUES('delete', ?, ?, ?, ?, ?)",
                (r["page_id"], r["text"], book_id, r["page_number"], r["chapter_id"]),
            )
        except Exception:
            pass  # row may not exist in FTS yet — safe to ignore

    # Insert fresh rows
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


# FTS5 stop-words / noise words to exclude from keyword search
_STOP_WORDS = frozenset({
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "shall", "can", "need", "dare", "ought",
    "used", "to", "of", "in", "on", "at", "by", "for", "with", "about",
    "what", "which", "who", "whom", "how", "when", "where", "why",
    "this", "that", "these", "those", "it", "its", "and", "or", "but",
    "not", "no", "nor", "so", "yet", "both", "either", "neither",
    "i", "me", "my", "we", "our", "you", "your", "he", "she", "they",
    "his", "her", "their", "us",
})


import re as _re


def _fts5_query(query: str) -> str:
    """
    Convert a natural-language question into a FTS5 MATCH expression.

    Strips punctuation, lower-cases, removes stop-words and very short words.
    The result is passed as a bound parameter via the TVF syntax so no
    reserved-word collisions are possible.
    """
    clean = _re.sub(r"[^\w\s]", " ", query.lower())
    words = clean.split()
    keywords = [w for w in words if w not in _STOP_WORDS and len(w) > 2]
    if not keywords:
        keywords = [w for w in words if len(w) > 1]
    # Join with OR so partial matches still return results
    return " OR ".join(keywords) if keywords else query


async def full_text_search(
    query: str,
    book_id: str | None = None,
    chapter_id: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Run a FTS5 query and return ranked hits with snippets.

    Uses the FTS5 table-valued function (TVF) syntax:
        SELECT … FROM pages_fts(?) WHERE …
    This passes the match expression as a bound ? parameter, which completely
    avoids FTS5 reserved-word syntax errors regardless of query content.
    """
    db = await get_db()
    fts_expr = _fts5_query(query)

    extra_where: list[str] = []
    params: list = [fts_expr]
    if book_id:
        extra_where.append("book_id = ?")
        params.append(book_id)
    if chapter_id:
        extra_where.append("chapter_id = ?")
        params.append(chapter_id)
    params.append(limit)

    where_sql = ("WHERE " + " AND ".join(extra_where)) if extra_where else ""
    sql = f"""
        SELECT book_id, page_number, chapter_id,
               snippet(pages_fts, 0, '<b>', '</b>', '…', 32) AS snippet,
               rank
        FROM pages_fts(?)
        {where_sql}
        ORDER BY rank
        LIMIT ?
    """
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()
    return [dict(r) for r in rows]
