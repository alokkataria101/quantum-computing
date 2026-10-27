"""app/routers/shared.py – admin-curated questions that students can see.

An admin generates questions (AI tab), optionally edits them, then shares them.
Shared questions are stored in the DB so they survive reloads and re-indexing.

GET    /books/{book_id}/chapters/{chapter_id}/shared   any logged-in user
POST   /books/{book_id}/chapters/{chapter_id}/shared   admin – share one or more
PUT    /shared/{share_id}                              admin – edit
DELETE /shared/{share_id}                              admin – unshare
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import User, require_admin, require_user
from ..database import get_db
from ..models import (
    SharedQuestion, SharedQuestionIn, SharedQuestionList, SharedQuestionsCreate,
)

router = APIRouter(tags=["shared questions"])


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_shared(r) -> SharedQuestion:
    return SharedQuestion(
        share_id=r["share_id"], book_id=r["book_id"], chapter_id=r["chapter_id"],
        type=r["question_type"], question=r["question"],
        options=json.loads(r["options"]) if r["options"] else None,
        answer=r["answer"], hint=r["hint"], page_start=r["page_start"],
        shared_by=r["shared_by"],
        shared_at=datetime.fromisoformat(r["shared_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
    )


@router.get(
    "/books/{book_id}/chapters/{chapter_id}/shared",
    response_model=SharedQuestionList,
    dependencies=[Depends(require_user)],
)
async def list_shared(book_id: str, chapter_id: str):
    db = await get_db()
    async with db.execute(
        "SELECT * FROM shared_questions WHERE book_id = ? AND chapter_id = ? "
        "ORDER BY shared_at, rowid",
        (book_id, chapter_id),
    ) as cur:
        rows = await cur.fetchall()
    qs = [_row_to_shared(r) for r in rows]
    return SharedQuestionList(questions=qs, total=len(qs))


@router.post(
    "/books/{book_id}/chapters/{chapter_id}/shared",
    response_model=SharedQuestionList,
    status_code=status.HTTP_201_CREATED,
)
async def share_questions(
    book_id: str,
    chapter_id: str,
    body: SharedQuestionsCreate,
    admin: User = Depends(require_admin),
):
    db = await get_db()
    async with db.execute(
        "SELECT 1 FROM chapters WHERE chapter_id = ? AND book_id = ?", (chapter_id, book_id)
    ) as cur:
        if not await cur.fetchone():
            raise HTTPException(status_code=404, detail="Chapter not found.")

    now = _now()
    ids: list[str] = []
    for q in body.questions:
        share_id = str(uuid.uuid4())
        ids.append(share_id)
        await db.execute(
            """INSERT INTO shared_questions
               (share_id, book_id, chapter_id, question_type, question, options,
                answer, hint, page_start, shared_by, shared_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (share_id, book_id, chapter_id, q.type, q.question,
             json.dumps(q.options) if q.options else None,
             q.answer, q.hint, q.page_start, admin.username, now, now),
        )
    await db.commit()

    placeholders = ",".join("?" * len(ids))
    async with db.execute(
        f"SELECT * FROM shared_questions WHERE share_id IN ({placeholders}) ORDER BY rowid", ids
    ) as cur:
        rows = await cur.fetchall()
    qs = [_row_to_shared(r) for r in rows]
    return SharedQuestionList(questions=qs, total=len(qs))


@router.put(
    "/shared/{share_id}",
    response_model=SharedQuestion,
    dependencies=[Depends(require_admin)],
)
async def edit_shared(share_id: str, body: SharedQuestionIn):
    db = await get_db()
    cur = await db.execute(
        """UPDATE shared_questions
           SET question_type = ?, question = ?, options = ?, answer = ?, hint = ?,
               page_start = ?, updated_at = ?
           WHERE share_id = ?""",
        (body.type, body.question, json.dumps(body.options) if body.options else None,
         body.answer, body.hint, body.page_start, _now(), share_id),
    )
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Shared question not found.")
    async with db.execute("SELECT * FROM shared_questions WHERE share_id = ?", (share_id,)) as c:
        return _row_to_shared(await c.fetchone())


@router.delete(
    "/shared/{share_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def unshare(share_id: str):
    db = await get_db()
    cur = await db.execute("DELETE FROM shared_questions WHERE share_id = ?", (share_id,))
    await db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Shared question not found.")
