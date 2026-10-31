"""app/routers/assignments.py – Assignment Builder and Worksheet Generator."""

from __future__ import annotations

import random
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

from ..auth import require_admin, require_user
from ..database import (
    add_questions_to_assignment_db,
    create_assignment_db,
    delete_assignment_db,
    get_assignment_db,
    get_db,
    list_assignments_db,
    remove_question_from_assignment_db,
    search_questions_db,
)
from ..models import (
    AssignmentAddQuestionsRequest,
    AssignmentAutoGenerateRequest,
    AssignmentCreate,
    AssignmentList,
    AssignmentRecord,
    ExportFormat,
    QuestionSearchQuery,
)

router = APIRouter(
    prefix="/api/v1/assignments",
    tags=["assignments"],
    dependencies=[Depends(require_user)],
)


@router.post(
    "",
    response_model=AssignmentRecord,
    dependencies=[Depends(require_admin)],
    summary="Create Assignment",
)
async def create_assignment(
    body: AssignmentCreate,
):
    db = await get_db()
    return await create_assignment_db(db, body)


@router.get(
    "",
    response_model=AssignmentList,
    summary="List Assignments",
)
async def list_assignments(
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    db = await get_db()
    assignments, total = await list_assignments_db(db, limit=limit, offset=offset)
    return AssignmentList(assignments=assignments, total=total)


@router.get(
    "/{assignment_id}",
    response_model=AssignmentRecord,
    summary="Get Assignment Details",
)
async def get_assignment(assignment_id: str):
    db = await get_db()
    assignment = await get_assignment_db(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@router.post(
    "/{assignment_id}/questions",
    response_model=AssignmentRecord,
    dependencies=[Depends(require_admin)],
    summary="Add Questions to Assignment",
)
async def add_questions_to_assignment(
    assignment_id: str,
    body: AssignmentAddQuestionsRequest,
):
    db = await get_db()
    updated = await add_questions_to_assignment_db(db, assignment_id, body.question_ids)
    if not updated:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return updated


@router.delete(
    "/{assignment_id}/questions/{question_id}",
    response_model=AssignmentRecord,
    dependencies=[Depends(require_admin)],
    summary="Remove Question from Assignment",
)
async def remove_question_from_assignment(
    assignment_id: str,
    question_id: str,
):
    db = await get_db()
    updated = await remove_question_from_assignment_db(db, assignment_id, question_id)
    if not updated:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return updated


@router.delete(
    "/{assignment_id}",
    dependencies=[Depends(require_admin)],
    summary="Delete Assignment",
)
async def delete_assignment(assignment_id: str):
    db = await get_db()
    deleted = await delete_assignment_db(db, assignment_id)
    return {"ok": True, "deleted": deleted}


@router.post(
    "/auto-generate",
    response_model=AssignmentRecord,
    dependencies=[Depends(require_admin)],
    summary="Auto-generate Assignment from Repository",
    description="Specifies class, subject, chapters, types, difficulty and builds a balanced assignment.",
)
async def auto_generate_assignment(
    body: AssignmentAutoGenerateRequest,
):
    db = await get_db()

    filters = QuestionSearchQuery(
        subject=body.subject,
        class_grade=body.class_grade,
        chapter_ids=body.chapter_ids if body.chapter_ids else None,
        question_types=body.question_types,
        difficulty=body.difficulty_levels,
        limit=100,
        offset=0,
    )
    candidates, _ = await search_questions_db(db, filters)
    if not candidates:
        raise HTTPException(
            status_code=404,
            detail="No matching questions found in repository for specified parameters.",
        )

    # Randomly select up to target total_questions
    random.shuffle(candidates)
    selected = candidates[: body.total_questions]
    selected_ids = [q.question_id for q in selected]

    assignment_data = AssignmentCreate(
        title=body.title,
        description=f"Auto-generated assignment with {len(selected_ids)} questions.",
        subject=body.subject,
        class_grade=body.class_grade,
        question_ids=selected_ids,
        target_marks=body.total_marks,
    )
    return await create_assignment_db(db, assignment_data)


@router.get(
    "/{assignment_id}/export",
    summary="Export Assignment (HTML / JSON / Markdown / Text)",
)
async def export_assignment(
    assignment_id: str,
    format: str = Query("html", description="Export format: html, json, md, text"),
    include_answers: bool = Query(False, description="Include answer key and solutions"),
):
    db = await get_db()
    assignment = await get_assignment_db(db, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if format == "json":
        return JSONResponse(assignment.model_dump(mode="json"))

    if format in ("md", "markdown"):
        lines = [
            f"# {assignment.title}",
            f"**Subject**: {assignment.subject or 'General'} | **Class**: {assignment.class_grade or 'N/A'} | **Total Marks**: {assignment.total_marks}",
            f"{assignment.description}\n",
            "---",
            "## Questions\n",
        ]
        for i, item in enumerate(assignment.questions, 1):
            q = item.question
            if not q:
                continue
            lines.append(f"**Q{i}.** ({q.marks} Marks) {q.question_text}")
            if q.options:
                for opt in q.options:
                    lines.append(f"- {opt}")
            if include_answers:
                if q.answer_text:
                    lines.append(f"\n*Answer*: {q.answer_text}")
                if q.solution_text:
                    lines.append(f"\n*Solution*: {q.solution_text}")
            lines.append("")
        return PlainTextResponse("\n".join(lines), media_type="text/markdown")

    # Default: Clean printable HTML worksheet
    q_html_parts = []
    for i, item in enumerate(assignment.questions, 1):
        q = item.question
        if not q:
            continue
        opts_html = ""
        if q.options:
            opts_li = "".join(f"<li style='margin-bottom:4px;'>{opt}</li>" for opt in q.options)
            opts_html = f"<ul style='list-style-type:none; padding-left:15px; margin-top:8px;'>{opts_li}</ul>"

        ans_html = ""
        if include_answers:
            ans_parts = []
            if q.answer_text:
                ans_parts.append(f"<div><strong>Answer:</strong> {q.answer_text}</div>")
            if q.solution_text:
                ans_parts.append(f"<div style='margin-top:4px;'><strong>Solution:</strong> {q.solution_text}</div>")
            if ans_parts:
                ans_html = f"<div style='margin-top:8px; padding:8px; background:#f0fdf4; border-left:3px solid #22c55e; font-size:0.9em;'>{''.join(ans_parts)}</div>"

        # If question has an image crop, embed it
        img_tag = ""
        if q.image_url:
            img_tag = f"<div style='margin:10px 0;'><img src='{q.image_url}' style='max-width:100%; border:1px solid #e2e8f0; border-radius:4px;'></div>"

        q_html_parts.append(f"""
        <div style="margin-bottom: 24px; padding-bottom: 16px; border-bottom: 1px dashed #e2e8f0; page-break-inside: avoid;">
            <div style="display:flex; justify-content:space-between; font-weight:600;">
                <span>Q{i}.</span>
                <span style="color:#64748b; font-size:0.9em;">[{q.marks} Marks]</span>
            </div>
            <div style="margin-top: 6px; font-size: 1.05em; line-height: 1.5;">{q.question_text}</div>
            {img_tag}
            {opts_html}
            {ans_html}
        </div>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{assignment.title}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; max-width: 800px; margin: 0 auto; padding: 32px 24px; color: #1e293b; background: #fff; }}
  .header {{ text-align: center; border-bottom: 2px solid #0f172a; padding-bottom: 16px; margin-bottom: 24px; }}
  .header h1 {{ margin: 0 0 8px; font-size: 1.6em; }}
  .meta {{ display: flex; justify-content: space-around; color: #475569; font-size: 0.95em; font-weight: 500; }}
  .student-info {{ display: flex; justify-content: space-between; margin: 20px 0 28px; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 0.9em; }}
  @media print {{
    body {{ padding: 0; }}
    @page {{ margin: 1.5cm; }}
  }}
</style>
</head>
<body>
  <div class="header">
    <h1>{assignment.title}</h1>
    <div class="meta">
      <span><strong>Subject:</strong> {assignment.subject or 'General'}</span>
      <span><strong>Class:</strong> {assignment.class_grade or 'N/A'}</span>
      <span><strong>Questions:</strong> {assignment.total_questions}</span>
      <span><strong>Total Marks:</strong> {assignment.total_marks}</span>
    </div>
  </div>
  <div class="student-info">
    <span>Student Name: _______________________</span>
    <span>Roll No: __________</span>
    <span>Date: ____________</span>
  </div>
  <div class="questions">
    {"".join(q_html_parts)}
  </div>
</body>
</html>"""

    return HTMLResponse(content=html_content)
