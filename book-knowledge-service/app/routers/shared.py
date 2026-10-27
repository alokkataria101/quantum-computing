"""app/routers/shared.py – admin-curated questions that students can see.

An admin generates questions (AI tab), optionally edits them, then shares them
with all students or with a chosen set of students. Shared questions are stored
in the DB so they survive reloads and re-indexing.

GET    /books/{book_id}/chapters/{chapter_id}/shared   any logged-in user
POST   /books/{book_id}/chapters/{chapter_id}/shared   admin – share one or more
PUT    /shared/{share_id}                              admin – edit
DELETE /shared/{share_id}                              admin – unshare
GET    /tasks                                          student – tasks assigned to me;
                                                       admin – every shared task

A shared question with no assignee rows is visible to every student; otherwise
only to the listed students.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status

from .. import auth
from ..auth import User, require_admin, require_user
from ..database import get_db
from ..models import (
    AssignedTask, AssignedTaskList, SharedQuestion, SharedQuestionIn,
    SharedQuestionList, SharedQuestionsCreate,
)

router = APIRouter(tags=["shared questions"])

# A student sees a share when it has no assignees, or they are one of them.
_VISIBLE_TO_STUDENT = (
    "(NOT EXISTS (SELECT 1 FROM shared_question_assignees a WHERE a.share_id = s.share_id) "
    "OR EXISTS (SELECT 1 FROM shared_question_assignees a "
    "WHERE a.share_id = s.share_id AND a.student = ?))"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _assignees(db, share_ids: list[str]) -> dict[str, list[str]]:
    if not share_ids:
        return {}
    marks = ",".join("?" * len(share_ids))
    out: dict[str, list[str]] = {}
    async with db.execute(
        f"SELECT share_id, student FROM shared_question_assignees "
        f"WHERE share_id IN ({marks}) ORDER BY student", share_ids
    ) as cur:
        for r in await cur.fetchall():
            out.setdefault(r["share_id"], []).append(r["student"])
    return out


def _shared_fields(r, assigned: dict[str, list[str]]) -> dict:
    return dict(
        share_id=r["share_id"], book_id=r["book_id"], chapter_id=r["chapter_id"],
        type=r["question_type"], question=r["question"],
        options=json.loads(r["options"]) if r["options"] else None,
        answer=r["answer"], hint=r["hint"], page_start=r["page_start"],
        shared_by=r["shared_by"],
        shared_at=datetime.fromisoformat(r["shared_at"]),
        updated_at=datetime.fromisoformat(r["updated_at"]),
        assigned_to=assigned.get(r["share_id"], []),
    )


def _row_to_shared(r, assigned: dict[str, list[str]]) -> SharedQuestion:
    return SharedQuestion(**_shared_fields(r, assigned))


@router.get(
    "/books/{book_id}/chapters/{chapter_id}/shared",
    response_model=SharedQuestionList,
)
async def list_shared(book_id: str, chapter_id: str, user: User = Depends(require_user)):
    db = await get_db()
    sql = "SELECT s.* FROM shared_questions s WHERE s.book_id = ? AND s.chapter_id = ?"
    params: list = [book_id, chapter_id]
    if not user.is_admin:
        sql += f" AND {_VISIBLE_TO_STUDENT}"
        params.append(user.username)
    sql += " ORDER BY s.shared_at, s.rowid"
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()
    assigned = await _assignees(db, [r["share_id"] for r in rows])
    qs = [_row_to_shared(r, assigned) for r in rows]
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

    targets: list[str] = []
    if body.students:
        known = set(auth.list_students())
        targets = sorted(set(body.students))
        unknown = [s for s in targets if s not in known]
        if unknown:
            raise HTTPException(status_code=400, detail=f"Unknown student(s): {', '.join(unknown)}")

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
        for student in targets:
            await db.execute(
                "INSERT INTO shared_question_assignees (share_id, student) VALUES (?, ?)",
                (share_id, student),
            )
    await db.commit()

    placeholders = ",".join("?" * len(ids))
    async with db.execute(
        f"SELECT * FROM shared_questions WHERE share_id IN ({placeholders}) ORDER BY rowid", ids
    ) as cur:
        rows = await cur.fetchall()
    assigned = await _assignees(db, ids)
    qs = [_row_to_shared(r, assigned) for r in rows]
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
        row = await c.fetchone()
    return _row_to_shared(row, await _assignees(db, [share_id]))


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


@router.get("/tasks", response_model=AssignedTaskList)
async def my_tasks(user: User = Depends(require_user)):
    """Everything shared with the caller, across all books (admins see all)."""
    db = await get_db()
    sql = (
        "SELECT s.*, b.title AS book_title, c.number AS chapter_number, c.title AS chapter_title "
        "FROM shared_questions s "
        "LEFT JOIN books b ON b.book_id = s.book_id "
        "LEFT JOIN chapters c ON c.chapter_id = s.chapter_id AND c.book_id = s.book_id"
    )
    params: list = []
    if not user.is_admin:
        sql += f" WHERE {_VISIBLE_TO_STUDENT}"
        params.append(user.username)
    sql += " ORDER BY s.shared_at DESC, s.rowid DESC"
    async with db.execute(sql, params) as cur:
        rows = await cur.fetchall()
    assigned = await _assignees(db, [r["share_id"] for r in rows])
    tasks = [
        AssignedTask(
            **_shared_fields(r, assigned),
            book_title=r["book_title"],
            chapter_number=r["chapter_number"],
            chapter_title=r["chapter_title"],
        )
        for r in rows
    ]
    return AssignedTaskList(tasks=tasks, total=len(tasks))
