"""app/database.py – SQLite + FTS5 setup with aiosqlite."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite

from .config import settings
from .models import (
    AssignmentCreate,
    AssignmentQuestionItem,
    AssignmentRecord,
    BoundingBox,
    DifficultyLevel,
    QuestionPatchRequest,
    QuestionRecord,
    QuestionSearchQuery,
    QuestionType,
    ReviewStatus,
)

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
    await _migrate(_DB)
    await _DB.commit()
    logger.info("Database initialised at %s", settings.database_path)


async def close_db() -> None:
    global _DB
    if _DB:
        await _DB.close()
        _DB = None


async def _migrate(db: aiosqlite.Connection) -> None:
    """Bring a database created by an older version up to date."""
    async with db.execute("PRAGMA table_info(chapters)") as cur:
        ch_cols = {r["name"] for r in await cur.fetchall()}
    if "printed_number" not in ch_cols:
        await db.execute("ALTER TABLE chapters ADD COLUMN printed_number INTEGER")

    # Migrate questions table for 3-layer representation & review studio
    async with db.execute("PRAGMA table_info(questions)") as cur:
        q_cols = {r["name"] for r in await cur.fetchall()}

    new_q_cols = {
        "options": "TEXT",
        "sub_parts": "TEXT",
        "hint": "TEXT",
        "bounding_box": "TEXT",
        "image_url": "TEXT",
        "image_path": "TEXT",
        "subject": "TEXT",
        "class_grade": "INTEGER",
        "topic": "TEXT",
        "difficulty": "TEXT DEFAULT 'medium'",
        "learning_outcome": "TEXT",
        "marks": "INTEGER DEFAULT 1",
        "tags": "TEXT",
        "review_status": "TEXT DEFAULT 'pending'",
        "content_hash": "TEXT",
        "source_question_id": "TEXT",
    }
    for col_name, col_type in new_q_cols.items():
        if col_name not in q_cols:
            await db.execute(f"ALTER TABLE questions ADD COLUMN {col_name} {col_type}")

    # Create indexes after guaranteeing columns exist
    await db.execute("CREATE INDEX IF NOT EXISTS idx_questions_subject ON questions(subject)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_questions_class ON questions(class_grade)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_questions_difficulty ON questions(difficulty)")
    await db.execute("CREATE INDEX IF NOT EXISTS idx_questions_review ON questions(review_status)")


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
        number        INTEGER NOT NULL,   -- 0 = front matter, then 1, 2, 3... in book order
        printed_number INTEGER,           -- number printed in the book (e.g. 23 in volume 2), if known
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
        hint               TEXT,
        options            TEXT,
        sub_parts          TEXT,
        page_start         INTEGER NOT NULL,
        page_end           INTEGER NOT NULL,
        confidence         REAL NOT NULL DEFAULT 1.0,
        extraction_method  TEXT NOT NULL DEFAULT 'pattern',
        bounding_box       TEXT,
        image_url          TEXT,
        image_path         TEXT,
        subject            TEXT,
        class_grade        INTEGER,
        topic              TEXT,
        difficulty         TEXT NOT NULL DEFAULT 'medium',
        learning_outcome   TEXT,
        marks              INTEGER NOT NULL DEFAULT 1,
        tags               TEXT,
        review_status      TEXT NOT NULL DEFAULT 'pending',
        content_hash       TEXT,
        source_question_id TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_questions_chapter ON questions(chapter_id);
    CREATE INDEX IF NOT EXISTS idx_questions_book ON questions(book_id);

    -- ── Assignments ───────────────────────────────────────────────────────────
    CREATE TABLE IF NOT EXISTS assignments (
        assignment_id    TEXT PRIMARY KEY,
        title            TEXT NOT NULL,
        description      TEXT NOT NULL DEFAULT '',
        subject          TEXT,
        class_grade      INTEGER,
        total_questions  INTEGER NOT NULL DEFAULT 0,
        total_marks      INTEGER NOT NULL DEFAULT 0,
        created_by       TEXT NOT NULL DEFAULT 'admin',
        created_at       TEXT NOT NULL,
        updated_at       TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS assignment_questions (
        assignment_id    TEXT NOT NULL REFERENCES assignments(assignment_id) ON DELETE CASCADE,
        question_id      TEXT NOT NULL REFERENCES questions(question_id) ON DELETE CASCADE,
        order_index      INTEGER NOT NULL DEFAULT 0,
        marks_override   INTEGER,
        PRIMARY KEY (assignment_id, question_id)
    );
    CREATE INDEX IF NOT EXISTS idx_assignment_questions_aid ON assignment_questions(assignment_id);

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

    -- ── Shared questions (admin-curated, visible to students) ─────────────────
    -- chapter_id is deliberately NOT a foreign key: re-indexing replaces chapter
    -- rows, which must not wipe questions an admin has edited and published.
    -- Deleting the book still removes them (book_id cascade).
    CREATE TABLE IF NOT EXISTS shared_questions (
        share_id      TEXT PRIMARY KEY,
        book_id       TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        chapter_id    TEXT NOT NULL,
        question_type TEXT NOT NULL DEFAULT 'question',
        question      TEXT NOT NULL,
        options       TEXT,
        answer        TEXT,
        hint          TEXT,
        page_start    INTEGER,
        shared_by     TEXT NOT NULL,
        shared_at     TEXT NOT NULL,
        updated_at    TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_shared_chapter ON shared_questions(book_id, chapter_id);

    -- Who a shared question is assigned to. No rows for a share_id = every student.
    CREATE TABLE IF NOT EXISTS shared_question_assignees (
        share_id  TEXT NOT NULL REFERENCES shared_questions(share_id) ON DELETE CASCADE,
        student   TEXT NOT NULL,
        PRIMARY KEY (share_id, student)
    );
    CREATE INDEX IF NOT EXISTS idx_assignee_student ON shared_question_assignees(student);

    -- ── Compiled PDFs history (every successful compile is recorded here) ───────
    -- Survives page refresh; admin can browse, download, or share any past compile.
    CREATE TABLE IF NOT EXISTS compiled_pdfs (
        compile_id      TEXT PRIMARY KEY,
        book_id         TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        job_id          TEXT NOT NULL,
        mode            TEXT NOT NULL DEFAULT 'questions',
        label           TEXT NOT NULL DEFAULT '',
        chapters_desc   TEXT NOT NULL DEFAULT '',   -- human-readable "Ch 1, 2, 3" or "All chapters"
        page_count      INTEGER NOT NULL DEFAULT 0,
        created_by      TEXT NOT NULL,
        created_at      TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_compiled_pdfs_book ON compiled_pdfs(book_id);

    -- ── Shared compiled PDFs (admin shares a compiled PDF with students) ────────
    CREATE TABLE IF NOT EXISTS shared_pdfs (
        share_id    TEXT PRIMARY KEY,
        book_id     TEXT NOT NULL REFERENCES books(book_id) ON DELETE CASCADE,
        job_id      TEXT NOT NULL,
        mode        TEXT NOT NULL DEFAULT 'questions',
        label       TEXT NOT NULL DEFAULT '',
        shared_by   TEXT NOT NULL,
        shared_at   TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_shared_pdfs_book ON shared_pdfs(book_id);

    -- Who a shared PDF is assigned to. No rows = every student.
    CREATE TABLE IF NOT EXISTS shared_pdf_assignees (
        share_id  TEXT NOT NULL REFERENCES shared_pdfs(share_id) ON DELETE CASCADE,
        student   TEXT NOT NULL,
        PRIMARY KEY (share_id, student)
    );
    CREATE INDEX IF NOT EXISTS idx_shared_pdf_assignee ON shared_pdf_assignees(student);
    """)


def row_to_question_record(row: aiosqlite.Row) -> QuestionRecord:
    """Convert a database row into a 3-layer QuestionRecord."""
    d = dict(row)

    # Parse options JSON
    options_raw = d.get("options")
    options = []
    if options_raw:
        try:
            options = json.loads(options_raw) if isinstance(options_raw, str) else options_raw
        except Exception:
            options = []

    # Parse sub_parts JSON
    sub_parts_raw = d.get("sub_parts")
    sub_parts = []
    if sub_parts_raw:
        try:
            sub_parts = json.loads(sub_parts_raw) if isinstance(sub_parts_raw, str) else sub_parts_raw
        except Exception:
            sub_parts = []

    # Parse tags JSON
    tags_raw = d.get("tags")
    tags = []
    if tags_raw:
        try:
            tags = json.loads(tags_raw) if isinstance(tags_raw, str) else tags_raw
        except Exception:
            tags = []

    # Parse bounding_box JSON
    bb_raw = d.get("bounding_box")
    bb = None
    if bb_raw:
        try:
            bb_dict = json.loads(bb_raw) if isinstance(bb_raw, str) else bb_raw
            if isinstance(bb_dict, dict) and "x0" in bb_dict:
                bb = BoundingBox(**bb_dict)
        except Exception:
            bb = None

    q_type_str = d.get("question_type", "exercise")
    try:
        q_type = QuestionType(q_type_str)
    except Exception:
        q_type = QuestionType.other

    diff_str = d.get("difficulty", "medium")
    try:
        diff = DifficultyLevel(diff_str)
    except Exception:
        diff = DifficultyLevel.medium

    rev_str = d.get("review_status", "pending")
    try:
        rev_status = ReviewStatus(rev_str)
    except Exception:
        rev_status = ReviewStatus.pending

    return QuestionRecord(
        question_id=d["question_id"],
        book_id=d["book_id"],
        chapter_id=d["chapter_id"],
        chapter_number=d.get("chapter_number", 0),
        question_type=q_type,
        question_number=d.get("question_number"),
        question_text=d["question_text"],
        options=options,
        sub_parts=sub_parts,
        solution_text=d.get("solution_text"),
        answer_text=d.get("answer_text"),
        hint=d.get("hint"),
        page_start=d["page_start"],
        page_end=d["page_end"],
        confidence=d.get("confidence", 1.0),
        extraction_method=d.get("extraction_method", "pattern"),
        bounding_box=bb,
        image_url=d.get("image_url"),
        image_path=d.get("image_path"),
        subject=d.get("subject"),
        class_grade=d.get("class_grade"),
        topic=d.get("topic"),
        difficulty=diff,
        learning_outcome=d.get("learning_outcome"),
        marks=d.get("marks", 1),
        tags=tags,
        review_status=rev_status,
        content_hash=d.get("content_hash"),
        source_question_id=d.get("source_question_id"),
        book_title=d.get("book_title"),
        chapter_title=d.get("chapter_title"),
    )


async def search_questions_db(
    db: aiosqlite.Connection,
    filters: QuestionSearchQuery,
) -> tuple[list[QuestionRecord], int]:
    """Execute dynamic multi-facet search on questions repository."""
    conditions = ["1=1"]
    params: list[Any] = []

    if filters.query:
        conditions.append("q.question_text LIKE ?")
        params.append(f"%{filters.query}%")

    if filters.book_ids:
        placeholders = ",".join("?" for _ in filters.book_ids)
        conditions.append(f"q.book_id IN ({placeholders})")
        params.extend(filters.book_ids)

    if filters.chapter_ids:
        placeholders = ",".join("?" for _ in filters.chapter_ids)
        conditions.append(f"q.chapter_id IN ({placeholders})")
        params.extend(filters.chapter_ids)

    if filters.subject:
        conditions.append("q.subject = ?")
        params.append(filters.subject)

    if filters.class_grade is not None:
        conditions.append("q.class_grade = ?")
        params.append(filters.class_grade)

    if filters.topics:
        placeholders = ",".join("?" for _ in filters.topics)
        conditions.append(f"q.topic IN ({placeholders})")
        params.extend(filters.topics)

    if filters.question_types:
        placeholders = ",".join("?" for _ in filters.question_types)
        conditions.append(f"q.question_type IN ({placeholders})")
        params.extend([qt.value for qt in filters.question_types])

    if filters.difficulty:
        placeholders = ",".join("?" for _ in filters.difficulty)
        conditions.append(f"q.difficulty IN ({placeholders})")
        params.extend([df.value for df in filters.difficulty])

    if filters.min_marks is not None:
        conditions.append("q.marks >= ?")
        params.append(filters.min_marks)

    if filters.max_marks is not None:
        conditions.append("q.marks <= ?")
        params.append(filters.max_marks)

    if filters.review_status:
        conditions.append("q.review_status = ?")
        params.append(filters.review_status.value)

    where_clause = " AND ".join(conditions)

    count_sql = f"""
        SELECT COUNT(*) as count
        FROM questions q
        WHERE {where_clause}
    """
    async with db.execute(count_sql, params) as cur:
        row = await cur.fetchone()
        total = row["count"] if row else 0

    query_sql = f"""
        SELECT q.*, b.title as book_title, c.title as chapter_title
        FROM questions q
        LEFT JOIN books b ON q.book_id = b.book_id
        LEFT JOIN chapters c ON q.chapter_id = c.chapter_id
        WHERE {where_clause}
        ORDER BY q.chapter_number ASC, q.page_start ASC, q.question_number ASC
        LIMIT ? OFFSET ?
    """
    query_params = list(params) + [filters.limit, filters.offset]

    async with db.execute(query_sql, query_params) as cur:
        rows = await cur.fetchall()
        questions = [row_to_question_record(r) for r in rows]

    return questions, total


async def get_question_by_id_db(
    db: aiosqlite.Connection,
    question_id: str,
) -> Optional[QuestionRecord]:
    sql = """
        SELECT q.*, b.title as book_title, c.title as chapter_title
        FROM questions q
        LEFT JOIN books b ON q.book_id = b.book_id
        LEFT JOIN chapters c ON q.chapter_id = c.chapter_id
        WHERE q.question_id = ?
    """
    async with db.execute(sql, [question_id]) as cur:
        row = await cur.fetchone()
        if row:
            return row_to_question_record(row)
    return None


async def update_question_db(
    db: aiosqlite.Connection,
    question_id: str,
    patch: QuestionPatchRequest,
) -> Optional[QuestionRecord]:
    updates: list[str] = []
    params: list[Any] = []

    if patch.question_text is not None:
        updates.append("question_text = ?")
        params.append(patch.question_text)

    if patch.question_type is not None:
        updates.append("question_type = ?")
        params.append(patch.question_type.value)

    if patch.question_number is not None:
        updates.append("question_number = ?")
        params.append(patch.question_number)

    if patch.options is not None:
        updates.append("options = ?")
        params.append(json.dumps(patch.options))

    if patch.sub_parts is not None:
        updates.append("sub_parts = ?")
        params.append(json.dumps(patch.sub_parts))

    if patch.answer_text is not None:
        updates.append("answer_text = ?")
        params.append(patch.answer_text)

    if patch.solution_text is not None:
        updates.append("solution_text = ?")
        params.append(patch.solution_text)

    if patch.hint is not None:
        updates.append("hint = ?")
        params.append(patch.hint)

    if patch.difficulty is not None:
        updates.append("difficulty = ?")
        params.append(patch.difficulty.value)

    if patch.marks is not None:
        updates.append("marks = ?")
        params.append(patch.marks)

    if patch.subject is not None:
        updates.append("subject = ?")
        params.append(patch.subject)

    if patch.class_grade is not None:
        updates.append("class_grade = ?")
        params.append(patch.class_grade)

    if patch.topic is not None:
        updates.append("topic = ?")
        params.append(patch.topic)

    if patch.learning_outcome is not None:
        updates.append("learning_outcome = ?")
        params.append(patch.learning_outcome)

    if patch.tags is not None:
        updates.append("tags = ?")
        params.append(json.dumps(patch.tags))

    if patch.review_status is not None:
        updates.append("review_status = ?")
        params.append(patch.review_status.value)

    if patch.bounding_box is not None:
        updates.append("bounding_box = ?")
        params.append(json.dumps(patch.bounding_box.model_dump()))

    if not updates:
        return await get_question_by_id_db(db, question_id)

    sql = f"UPDATE questions SET {', '.join(updates)} WHERE question_id = ?"
    params.append(question_id)
    await db.execute(sql, params)
    await db.commit()

    return await get_question_by_id_db(db, question_id)


# ── Assignment DB Operations ──────────────────────────────────────────────────

async def create_assignment_db(
    db: aiosqlite.Connection,
    data: AssignmentCreate,
    created_by: str = "admin",
) -> AssignmentRecord:
    assignment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Calculate questions and total marks
    total_marks = 0
    question_items = []

    if data.question_ids:
        for idx, qid in enumerate(data.question_ids):
            q = await get_question_by_id_db(db, qid)
            marks = q.marks if q else 1
            total_marks += marks
            question_items.append(
                AssignmentQuestionItem(
                    question_id=qid,
                    order_index=idx,
                    marks_override=None,
                    question=q,
                )
            )

    sql = """
        INSERT INTO assignments (
            assignment_id, title, description, subject, class_grade,
            total_questions, total_marks, created_by, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    await db.execute(
        sql,
        (
            assignment_id,
            data.title,
            data.description,
            data.subject,
            data.class_grade,
            len(data.question_ids),
            total_marks,
            created_by,
            now,
            now,
        ),
    )

    for item in question_items:
        await db.execute(
            """
            INSERT OR REPLACE INTO assignment_questions (
                assignment_id, question_id, order_index, marks_override
            ) VALUES (?, ?, ?, ?)
            """,
            (assignment_id, item.question_id, item.order_index, item.marks_override),
        )

    await db.commit()

    return AssignmentRecord(
        assignment_id=assignment_id,
        title=data.title,
        description=data.description,
        subject=data.subject,
        class_grade=data.class_grade,
        total_questions=len(data.question_ids),
        total_marks=total_marks,
        questions=question_items,
        created_by=created_by,
        created_at=datetime.fromisoformat(now),
        updated_at=datetime.fromisoformat(now),
    )


async def get_assignment_db(
    db: aiosqlite.Connection,
    assignment_id: str,
) -> Optional[AssignmentRecord]:
    async with db.execute(
        "SELECT * FROM assignments WHERE assignment_id = ?", [assignment_id]
    ) as cur:
        row = await cur.fetchone()
        if not row:
            return None

    d = dict(row)

    # Fetch associated questions
    q_sql = """
        SELECT aq.order_index, aq.marks_override, aq.question_id
        FROM assignment_questions aq
        WHERE aq.assignment_id = ?
        ORDER BY aq.order_index ASC
    """
    items = []
    total_marks = 0
    async with db.execute(q_sql, [assignment_id]) as cur:
        q_rows = await cur.fetchall()
        for qr in q_rows:
            q_rec = await get_question_by_id_db(db, qr["question_id"])
            m = qr["marks_override"] if qr["marks_override"] is not None else (q_rec.marks if q_rec else 1)
            total_marks += m
            items.append(
                AssignmentQuestionItem(
                    question_id=qr["question_id"],
                    order_index=qr["order_index"],
                    marks_override=qr["marks_override"],
                    question=q_rec,
                )
            )

    return AssignmentRecord(
        assignment_id=d["assignment_id"],
        title=d["title"],
        description=d.get("description", ""),
        subject=d.get("subject"),
        class_grade=d.get("class_grade"),
        total_questions=len(items),
        total_marks=total_marks,
        questions=items,
        created_by=d.get("created_by", "admin"),
        created_at=datetime.fromisoformat(d["created_at"]),
        updated_at=datetime.fromisoformat(d["updated_at"]),
    )


async def list_assignments_db(
    db: aiosqlite.Connection,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[AssignmentRecord], int]:
    async with db.execute("SELECT COUNT(*) as count FROM assignments") as cur:
        row = await cur.fetchone()
        total = row["count"] if row else 0

    sql = "SELECT assignment_id FROM assignments ORDER BY created_at DESC LIMIT ? OFFSET ?"
    assignments = []
    async with db.execute(sql, [limit, offset]) as cur:
        rows = await cur.fetchall()
        for r in rows:
            rec = await get_assignment_db(db, r["assignment_id"])
            if rec:
                assignments.append(rec)

    return assignments, total


async def add_questions_to_assignment_db(
    db: aiosqlite.Connection,
    assignment_id: str,
    question_ids: list[str],
) -> Optional[AssignmentRecord]:
    assignment = await get_assignment_db(db, assignment_id)
    if not assignment:
        return None

    existing_qids = {item.question_id for item in assignment.questions}
    next_index = len(assignment.questions)

    for qid in question_ids:
        if qid not in existing_qids:
            await db.execute(
                """
                INSERT OR REPLACE INTO assignment_questions (
                    assignment_id, question_id, order_index
                ) VALUES (?, ?, ?)
                """,
                (assignment_id, qid, next_index),
            )
            next_index += 1

    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "UPDATE assignments SET updated_at = ? WHERE assignment_id = ?",
        (now, assignment_id),
    )
    await db.commit()
    return await get_assignment_db(db, assignment_id)


async def remove_question_from_assignment_db(
    db: aiosqlite.Connection,
    assignment_id: str,
    question_id: str,
) -> Optional[AssignmentRecord]:
    await db.execute(
        "DELETE FROM assignment_questions WHERE assignment_id = ? AND question_id = ?",
        (assignment_id, question_id),
    )
    now = datetime.now(timezone.utc).isoformat()
    await db.execute(
        "UPDATE assignments SET updated_at = ? WHERE assignment_id = ?",
        (now, assignment_id),
    )
    await db.commit()
    return await get_assignment_db(db, assignment_id)


async def delete_assignment_db(
    db: aiosqlite.Connection,
    assignment_id: str,
) -> bool:
    await db.execute("DELETE FROM assignments WHERE assignment_id = ?", (assignment_id,))
    await db.commit()
    return True
