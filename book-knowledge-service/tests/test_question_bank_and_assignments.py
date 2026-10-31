"""tests/test_question_bank_and_assignments.py – tests for Visual Question Bank, Review Studio, and Assignment Builder."""

import json
import pytest
import uuid
from app.database import get_db, search_questions_db, get_question_by_id_db, update_question_db
from app.models import QuestionRecord, QuestionType, DifficultyLevel, ReviewStatus


async def _insert_test_question(db, q: QuestionRecord):
    await db.execute(
        """INSERT INTO questions
           (question_id, book_id, chapter_id, chapter_number, question_type,
            question_number, question_text, solution_text, answer_text,
            hint, options, sub_parts, page_start, page_end, confidence,
            extraction_method, bounding_box, image_url, image_path,
            difficulty, marks, content_hash, review_status)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            q.question_id,
            q.book_id,
            q.chapter_id,
            q.chapter_number,
            q.question_type.value if hasattr(q.question_type, "value") else str(q.question_type),
            q.question_number,
            q.question_text,
            q.solution_text,
            q.answer_text,
            q.hint,
            json.dumps(q.options) if q.options else None,
            json.dumps(q.sub_parts) if q.sub_parts else None,
            q.page_start,
            q.page_end,
            q.confidence,
            q.extraction_method,
            json.dumps(q.bounding_box.model_dump()) if q.bounding_box else None,
            q.image_url,
            q.image_path,
            q.difficulty.value if hasattr(q.difficulty, "value") else str(q.difficulty),
            q.marks,
            q.content_hash,
            q.review_status.value if hasattr(q.review_status, "value") else str(q.review_status),
        ),
    )
    await db.commit()


@pytest.mark.asyncio
async def test_question_bank_crud_and_search(client):
    db = await get_db()
    book_id = "test-bank-book-1"
    
    # Insert dummy book and chapter for foreign keys
    await db.execute(
        "INSERT INTO books (book_id, filename, title, author, total_pages, file_size, sha256, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (book_id, "physics.pdf", "Physics Grade 10", "Author X", 100, 1024, "dummy-sha-1", "indexed", "2026-01-01T00:00:00")
    )
    await db.execute(
        "INSERT INTO chapters (chapter_id, book_id, number, title, page_start, page_end) VALUES (?,?,?,?,?,?)",
        ("ch-1", book_id, 1, "Electric Current", 1, 10)
    )
    await db.commit()

    # Create questions with rich metadata
    q1 = QuestionRecord(
        question_id=str(uuid.uuid4()),
        book_id=book_id,
        chapter_id="ch-1",
        chapter_number=1,
        page_start=5,
        page_end=5,
        question_number="1",
        question_text="What is the unit of electric current?",
        question_type=QuestionType.mcq,
        options=["(A) Volt", "(B) Ampere", "(C) Ohm", "(D) Watt"],
        difficulty=DifficultyLevel.easy,
        marks=1,
        review_status=ReviewStatus.approved
    )
    q2 = QuestionRecord(
        question_id=str(uuid.uuid4()),
        book_id=book_id,
        chapter_id="ch-1",
        chapter_number=1,
        page_start=6,
        page_end=6,
        question_number="2",
        question_text="Calculate the acceleration when force is 10N and mass is 2kg.",
        question_type=QuestionType.numerical,
        difficulty=DifficultyLevel.medium,
        marks=3,
        review_status=ReviewStatus.pending
    )
    await _insert_test_question(db, q1)
    await _insert_test_question(db, q2)

    # Search via REST API
    res = await client.get("/api/v1/questions/search?question_type=mcq")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["questions"][0]["question_id"] == q1.question_id
    assert len(data["questions"][0]["options"]) == 4

    # Search by text query
    res2 = await client.get("/api/v1/questions/search?query=acceleration")
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["total"] == 1
    assert data2["questions"][0]["question_id"] == q2.question_id

    # PATCH question (Review Studio action)
    patch_res = await client.patch(
        f"/api/v1/questions/{q2.question_id}",
        json={"review_status": "approved", "marks": 5, "difficulty": "hard"}
    )
    assert patch_res.status_code == 200
    patched_q = patch_res.json()
    assert patched_q["review_status"] == "approved"
    assert patched_q["marks"] == 5
    assert patched_q["difficulty"] == "hard"


@pytest.mark.asyncio
async def test_assignment_builder_and_exports(client):
    db = await get_db()
    book_id = "test-assignment-book"
    
    await db.execute(
        "INSERT INTO books (book_id, filename, title, author, total_pages, file_size, sha256, status, created_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (book_id, "math.pdf", "Mathematics Standard", "Author Y", 50, 2048, "dummy-sha-2", "indexed", "2026-01-01T00:00:00")
    )
    await db.execute(
        "INSERT INTO chapters (chapter_id, book_id, number, title, page_start, page_end) VALUES (?,?,?,?,?,?)",
        ("ch-m1", book_id, 1, "Real Numbers", 1, 10)
    )
    await db.commit()

    q1 = QuestionRecord(
        question_id=str(uuid.uuid4()),
        book_id=book_id,
        chapter_id="ch-m1",
        chapter_number=1,
        page_start=1,
        page_end=1,
        question_number="1",
        question_text="Solve for x: 2x + 4 = 10",
        question_type=QuestionType.short_answer,
        difficulty=DifficultyLevel.easy,
        marks=2,
        review_status=ReviewStatus.approved
    )
    q2 = QuestionRecord(
        question_id=str(uuid.uuid4()),
        book_id=book_id,
        chapter_id="ch-m1",
        chapter_number=1,
        page_start=2,
        page_end=2,
        question_number="2",
        question_text="Prove that the square root of 2 is irrational.",
        question_type=QuestionType.long_answer,
        difficulty=DifficultyLevel.hard,
        marks=5,
        review_status=ReviewStatus.approved
    )
    await _insert_test_question(db, q1)
    await _insert_test_question(db, q2)

    # 1. Create assignment manually
    payload = {
        "title": "Algebra & Proofs Homework",
        "description": "Weekly homework set",
        "subject": "Mathematics",
        "target_grade": "Grade 10",
        "question_ids": [q1.question_id, q2.question_id]
    }
    create_res = await client.post("/api/v1/assignments", json=payload)
    assert create_res.status_code in (200, 201)
    asgn = create_res.json()
    asgn_id = asgn["assignment_id"]
    assert asgn["total_marks"] == 7
    assert len(asgn["questions"]) == 2

    # 2. Export HTML Worksheet
    export_html = await client.get(f"/api/v1/assignments/{asgn_id}/export?format=html")
    assert export_html.status_code == 200
    assert "text/html" in export_html.headers.get("content-type", "")
    assert "Algebra &amp; Proofs Homework" in export_html.text or "Algebra & Proofs Homework" in export_html.text

    # 3. Export Markdown Worksheet
    export_md = await client.get(f"/api/v1/assignments/{asgn_id}/export?format=markdown")
    assert export_md.status_code == 200
    assert "# Algebra & Proofs Homework" in export_md.text

    # 4. Auto-generate assignment
    auto_res = await client.post("/api/v1/assignments/auto-generate", json={
        "title": "Auto Generated Math Quiz",
        "chapter_ids": ["ch-m1"],
        "difficulty_levels": ["easy"],
        "total_questions": 5
    })
    assert auto_res.status_code in (200, 201)
    auto_data = auto_res.json()
    assert auto_data["title"] == "Auto Generated Math Quiz"
    assert len(auto_data["questions"]) >= 1


@pytest.mark.asyncio
async def test_ui_routes_accessible(client):
    # UI Question bank
    r1 = await client.get("/ui/question-bank")
    assert r1.status_code == 200
    assert "Universal Question Bank" in r1.text

    # UI Exam Draft
    r2 = await client.get("/ui/exam-draft")
    assert r2.status_code == 200
