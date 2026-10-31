"""app/routers/exam_drafts.py – Exam Draft (Exam Paper in preparation) endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from ..auth import User, require_admin, require_user
from ..database import (
    add_questions_to_exam_draft_db,
    create_exam_draft_db,
    delete_exam_draft_db,
    get_db,
    get_exam_draft_db,
    get_exam_drafts_for_student_db,
    get_or_create_active_draft_db,
    list_exam_drafts_db,
    patch_exam_draft_db,
    patch_exam_draft_item_db,
    remove_question_from_exam_draft_db,
    share_exam_draft_db,
)
from ..models import (
    ExamDraftAddQuestionsRequest,
    ExamDraftCreate,
    ExamDraftItemPatch,
    ExamDraftList,
    ExamDraftPatch,
    ExamDraftRecord,
    ExamDraftStatus,
    ExamShareRequest,
)

router = APIRouter(
    prefix="/api/v1/exam-drafts",
    tags=["exam-drafts"],
    dependencies=[Depends(require_user)],
)


# ── Active draft (auto-create) ────────────────────────────────────────────────

@router.get(
    "/active",
    response_model=ExamDraftRecord,
    summary="Get the current active draft (creates one if none exists)",
)
async def get_active_draft(user: User = Depends(require_user)):
    db = await get_db()
    return await get_or_create_active_draft_db(db, user.username)


# ── CRUD ──────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ExamDraftRecord,
    dependencies=[Depends(require_admin)],
)
async def create_draft(body: ExamDraftCreate, user: User = Depends(require_admin)):
    db = await get_db()
    return await create_exam_draft_db(db, body, user.username)


@router.get("", response_model=ExamDraftList)
async def list_drafts(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db = await get_db()
    drafts, total = await list_exam_drafts_db(db, limit=limit, offset=offset)
    return ExamDraftList(drafts=drafts, total=total)


@router.get("/my-exams", summary="Shared exams visible to the current student")
async def my_exams(user: User = Depends(require_user)):
    db = await get_db()
    drafts = await get_exam_drafts_for_student_db(db, user.username)
    return {"drafts": [d.model_dump(mode="json") for d in drafts], "total": len(drafts)}


@router.get("/{draft_id}", response_model=ExamDraftRecord)
async def get_draft(draft_id: str):
    db = await get_db()
    draft = await get_exam_draft_db(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.patch(
    "/{draft_id}",
    response_model=ExamDraftRecord,
    dependencies=[Depends(require_admin)],
)
async def patch_draft(draft_id: str, body: ExamDraftPatch):
    db = await get_db()
    draft = await patch_exam_draft_db(db, draft_id, body)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.delete("/{draft_id}", dependencies=[Depends(require_admin)])
async def delete_draft(draft_id: str):
    db = await get_db()
    await delete_exam_draft_db(db, draft_id)
    return {"ok": True}


# ── Question management ───────────────────────────────────────────────────────

@router.post(
    "/{draft_id}/questions",
    response_model=ExamDraftRecord,
    dependencies=[Depends(require_admin)],
    summary="Add one or more questions to the draft",
)
async def add_questions(draft_id: str, body: ExamDraftAddQuestionsRequest):
    db = await get_db()
    draft = await add_questions_to_exam_draft_db(
        db, draft_id, body.question_ids, body.include_answer
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.patch(
    "/{draft_id}/items/{item_id}",
    response_model=ExamDraftRecord,
    dependencies=[Depends(require_admin)],
    summary="Edit marks, question number, text or answer for one item",
)
async def patch_item(draft_id: str, item_id: str, body: ExamDraftItemPatch):
    db = await get_db()
    ok = await patch_exam_draft_item_db(db, item_id, body)
    if not ok:
        raise HTTPException(status_code=404, detail="Item not found")
    draft = await get_exam_draft_db(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.delete(
    "/{draft_id}/items/{item_id}",
    response_model=ExamDraftRecord,
    dependencies=[Depends(require_admin)],
    summary="Remove a question from the draft",
)
async def remove_item(draft_id: str, item_id: str):
    db = await get_db()
    draft = await remove_question_from_exam_draft_db(db, draft_id, item_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


# ── Approve & Share ───────────────────────────────────────────────────────────

@router.post(
    "/{draft_id}/approve",
    response_model=ExamDraftRecord,
    dependencies=[Depends(require_admin)],
    summary="Approve the draft — makes it ready for PDF download and sharing",
)
async def approve_draft(draft_id: str):
    db = await get_db()
    draft = await patch_exam_draft_db(
        db, draft_id, ExamDraftPatch(status=ExamDraftStatus.approved)
    )
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    return draft


@router.post(
    "/{draft_id}/share",
    response_model=ExamDraftRecord,
    dependencies=[Depends(require_admin)],
    summary="Share the approved exam with students",
)
async def share_draft(draft_id: str, body: ExamShareRequest = ExamShareRequest()):
    db = await get_db()
    draft = await get_exam_draft_db(db, draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    if draft.status == ExamDraftStatus.draft:
        raise HTTPException(
            status_code=400,
            detail="Approve the exam first before sharing.",
        )
    return await share_exam_draft_db(db, draft_id, body.students)
