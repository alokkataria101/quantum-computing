"""app/database.py – SQLite + FTS5 setup with aiosqlite."""

from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from .config import settings

logger = logging.getLogger(__name__)

_DB: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    global _DB
    if _DB is None:
        raise RuntimeError("Database not initialised. Call init_db() at startup.")
    return _DB


async def init_db() -> None:
    global _DB
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    _DB = await aiosqlite.connect(settings.database_path)
    _DB.row_factory = aiosqlite.Row
    await _DB.execute("PRAGMA journal_mode=WAL")
    await _DB.execute("PRAGMA foreign_keys=ON")
    await _create_schema(_DB)
    await _DB.commit()
    logger.info("Database initialised at %s", settings.database_path)


async def close_db() -> None:
    global _DB
    if _DB:
        await _DB.close()
        _DB = None


async def _create_schema(db: aiosqlite.Connection) -> None:
    await db.executescript("""
    -- ── Books ────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS books (
        book_id       TEXT PRIMARY KEY,
        filename      TEXT NOT NULL,
        title         TEXT NOT NULL DEFAULT '',
        author        TEXT NOT NULL DEFAULT '',
        sha256        TEXT NOT NULL UNIQUE,
        file_size     INTEGER NOT NULL,
        total_pages   INTEGER NOT NULL DEFAULT 0,
        status        TEXT NOT NULL DEFAULT 'uploaded',
        error_message TEXT,
        created_at    TEXT NOT NULL,
        indexed_at    TEXT
    );

    -- ── Chapters ─────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS chapters (
        chapter_id    TEXT PRIMARY KEY,
        book_id       TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        number        INTEGER NOT NULL,
        title         TEXT NOT NULL,
        page_start    INTEGER NOT NULL,
        page_end      INTEGER NOT NULL,
        confidence    REAL NOT NULL DEFAULT 1.0,
        source        TEXT NOT NULL DEFAULT 'toc'
    );
    CREATE INDEX IF NOT EXISTS idx_chapters_book ON chapters(book_id);

    -- ── Pages ─────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS pages (
        page_id       INTEGER PRIMARY KEY AUTOINCREMENT,
        book_id       TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        page_number   INTEGER NOT NULL,
        text          TEXT NOT NULL DEFAULT '',
        has_images    INTEGER NOT NULL DEFAULT 0,
        is_scanned    INTEGER NOT NULL DEFAULT 0,
        ocr_used      INTEGER NOT NULL DEFAULT 0,
        chapter_id    TEXT REFERENCES chapters(chapter_id)
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_pages_book_page ON pages(book_id, page_number);
    CREATE INDEX IF NOT EXISTS idx_pages_chapter ON pages(chapter_id);

    -- ── FTS5 full-text index ──────────────────────────────────────────────────
    CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
        text,
        book_id UNINDEXED,
        page_number UNINDEXED,
        chapter_id UNINDEXED,
        content='pages',
        content_rowid='page_id'
    );

    -- ── Questions ─────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS questions (
        question_id        TEXT PRIMARY KEY,
        book_id            TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        chapter_id         TEXT NOT NULL REFERENCES chapters(chapter_id) ON DELETE CASCADE,
        chapter_number     INTEGER NOT NULL,
        question_type      TEXT NOT NULL,
        question_number    TEXT,
        question_text      TEXT NOT NULL,
        solution_text      TEXT,
        answer_text        TEXT,
        page_start         INTEGER NOT NULL,
        page_end           INTEGER NOT NULL,
        confidence         REAL NOT NULL DEFAULT 1.0,
        extraction_method  TEXT NOT NULL DEFAULT 'pattern'
    );
    CREATE INDEX IF NOT EXISTS idx_questions_chapter ON questions(chapter_id);
    CREATE INDEX IF NOT EXISTS idx_questions_book ON questions(book_id);

    -- ── Figures ───────────────────────────────────────────────────────────────
    -- One row per figure caption found in the PDF.
    -- bbox_* are in PDF points (pts), matching the coordinate space of fitz.Rect.
    CREATE TABLE IF NOT EXISTS figures (
        figure_id   TEXT PRIMARY KEY,   -- book_id + '_' + fig_num  e.g. "abc123_8.10"
        book_id     TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        fig_num     TEXT NOT NULL,      -- normalised label, e.g. "8.10" or "3.1"
        page        INTEGER NOT NULL,   -- 1-based page number
        bbox_x0     REAL NOT NULL,      -- crop rect in PDF pts
        bbox_y0     REAL NOT NULL,
        bbox_x1     REAL NOT NULL,
        bbox_y1     REAL NOT NULL
    );
    CREATE UNIQUE INDEX IF NOT EXISTS idx_figures_book_num ON figures(book_id, fig_num);
    CREATE INDEX IF NOT EXISTS idx_figures_book ON figures(book_id);

    -- ── Jobs ──────────────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS jobs (
        job_id      TEXT PRIMARY KEY,
        job_type    TEXT NOT NULL,
        book_id     TEXT NOT NULL,
        chapter_id  TEXT,
        status      TEXT NOT NULL DEFAULT 'pending',
        progress    REAL NOT NULL DEFAULT 0.0,
        message     TEXT NOT NULL DEFAULT '',
        error       TEXT,
        created_at  TEXT NOT NULL,
        updated_at  TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_jobs_book ON jobs(book_id);
    """)
