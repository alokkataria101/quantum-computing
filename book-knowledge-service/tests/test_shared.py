"""tests/test_shared.py – admin shares generated questions; students view them."""

import io
import re

import pytest

from app import auth as auth_module
from app.database import get_db

pytestmark = pytest.mark.asyncio

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
)

MCQ = {
    "question": "What is the SI unit of force?",
    "type": "mcq",
    "options": ["A. Joule", "B. Newton", "C. Watt", "D. Pascal"],
    "answer": "B. Newton",
    "hint": "F = ma",
    "page_start": 1,
}


async def _make_chapter(client, chapter_id="ch1"):
    """Upload a book and give it one chapter. Returns (book_id, chapter_id)."""
    r = await client.post("/books", files={"file": ("s.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")})
    book_id = r.json()["book_id"]
    db = await get_db()
    await db.execute(
        "INSERT INTO chapters (chapter_id, book_id, number, title, page_start, page_end) "
        "VALUES (?, ?, 1, 'Mechanics', 1, 1)", (chapter_id, book_id))
    await db.commit()
    return book_id, chapter_id


def _url(book_id, chapter_id):
    return f"/books/{book_id}/chapters/{chapter_id}/shared"


async def _switch_to_student(client):
    await client.post("/auth/logout")
    auth_module.add_student("pupil", "pupilpass")
    r = await client.post("/auth/login", json={"username": "pupil", "password": "pupilpass", "role": "student"})
    assert r.status_code == 200


# ── Share / list ──────────────────────────────────────────────────────────────

async def test_empty_by_default(client):
    book_id, ch = await _make_chapter(client)
    r = await client.get(_url(book_id, ch))
    assert r.status_code == 200
    assert r.json() == {"questions": [], "total": 0}


async def test_admin_shares_and_student_sees_it(client):
    book_id, ch = await _make_chapter(client)
    r = await client.post(_url(book_id, ch), json={"questions": [MCQ]})
    assert r.status_code == 201
    shared = r.json()["questions"][0]
    assert shared["question"] == MCQ["question"]
    assert shared["options"] == MCQ["options"]
    assert shared["answer"] == "B. Newton"
    assert shared["shared_by"] == "admin"
    assert shared["share_id"]

    await _switch_to_student(client)
    got = (await client.get(_url(book_id, ch))).json()
    assert got["total"] == 1
    assert got["questions"][0]["question"] == MCQ["question"]
    assert got["questions"][0]["options"] == MCQ["options"]


async def test_share_several_at_once_keeps_order(client):
    book_id, ch = await _make_chapter(client)
    qs = [{"question": f"Question {i}"} for i in range(5)]
    r = await client.post(_url(book_id, ch), json={"questions": qs})
    assert [q["question"] for q in r.json()["questions"]] == [f"Question {i}" for i in range(5)]
    listed = (await client.get(_url(book_id, ch))).json()["questions"]
    assert [q["question"] for q in listed] == [f"Question {i}" for i in range(5)]


async def test_shared_is_scoped_to_its_chapter(client):
    book_id, ch1 = await _make_chapter(client)
    db = await get_db()
    await db.execute(
        "INSERT INTO chapters (chapter_id, book_id, number, title, page_start, page_end) "
        "VALUES ('ch2', ?, 2, 'Waves', 1, 1)", (book_id,))
    await db.commit()
    await client.post(_url(book_id, ch1), json={"questions": [MCQ]})
    assert (await client.get(_url(book_id, "ch2"))).json()["total"] == 0


async def test_optional_fields_can_be_omitted(client):
    book_id, ch = await _make_chapter(client)
    r = await client.post(_url(book_id, ch), json={"questions": [{"question": "Just text?"}]})
    q = r.json()["questions"][0]
    assert q["type"] == "question"
    assert q["options"] is None and q["answer"] is None and q["hint"] is None


# ── Validation ────────────────────────────────────────────────────────────────

async def test_share_unknown_chapter_404(client):
    book_id, _ = await _make_chapter(client)
    r = await client.post(_url(book_id, "nope"), json={"questions": [MCQ]})
    assert r.status_code == 404


@pytest.mark.parametrize("body", [
    {"questions": []},                                  # nothing to share
    {"questions": [{"question": "   "}]},               # blank after trim
    {"questions": [{"question": ""}]},
    {"questions": [{"question": "ok", "page_start": 0}]},
    {"questions": [{"question": "ok", "options": ["x"] * 11}]},
    {"questions": [{"question": "x" * 5001}]},
    {},
])
async def test_share_rejects_bad_payload(client, body):
    book_id, ch = await _make_chapter(client)
    r = await client.post(_url(book_id, ch), json=body)
    assert r.status_code == 422
    assert (await client.get(_url(book_id, ch))).json()["total"] == 0


# ── Edit / unshare ────────────────────────────────────────────────────────────

async def test_admin_edits_shared_question(client):
    book_id, ch = await _make_chapter(client)
    sid = (await client.post(_url(book_id, ch), json={"questions": [MCQ]})).json()["questions"][0]["share_id"]

    edited = dict(MCQ, question="Which unit measures force?", answer="Newton", options=None, hint=None)
    r = await client.put(f"/shared/{sid}", json=edited)
    assert r.status_code == 200
    body = r.json()
    assert body["question"] == "Which unit measures force?"
    assert body["answer"] == "Newton"
    assert body["options"] is None and body["hint"] is None
    assert body["share_id"] == sid

    await _switch_to_student(client)
    seen = (await client.get(_url(book_id, ch))).json()["questions"][0]
    assert seen["question"] == "Which unit measures force?"


async def test_edit_unknown_share_404(client):
    r = await client.put("/shared/does-not-exist", json={"question": "Q?"})
    assert r.status_code == 404


async def test_edit_rejects_blank_question(client):
    book_id, ch = await _make_chapter(client)
    sid = (await client.post(_url(book_id, ch), json={"questions": [MCQ]})).json()["questions"][0]["share_id"]
    assert (await client.put(f"/shared/{sid}", json={"question": "  "})).status_code == 422
    # The stored question is untouched.
    assert (await client.get(_url(book_id, ch))).json()["questions"][0]["question"] == MCQ["question"]


async def test_admin_unshares_and_student_no_longer_sees_it(client):
    book_id, ch = await _make_chapter(client)
    ids = [q["share_id"] for q in (await client.post(
        _url(book_id, ch), json={"questions": [{"question": "A?"}, {"question": "B?"}]}
    )).json()["questions"]]

    assert (await client.delete(f"/shared/{ids[0]}")).status_code == 204
    assert (await client.delete(f"/shared/{ids[0]}")).status_code == 404

    await _switch_to_student(client)
    left = (await client.get(_url(book_id, ch))).json()["questions"]
    assert [q["question"] for q in left] == ["B?"]


# ── Roles ─────────────────────────────────────────────────────────────────────

async def test_student_cannot_share_edit_or_unshare(client):
    book_id, ch = await _make_chapter(client)
    sid = (await client.post(_url(book_id, ch), json={"questions": [MCQ]})).json()["questions"][0]["share_id"]
    await _switch_to_student(client)

    assert (await client.post(_url(book_id, ch), json={"questions": [MCQ]})).status_code == 403
    assert (await client.put(f"/shared/{sid}", json={"question": "hacked"})).status_code == 403
    assert (await client.delete(f"/shared/{sid}")).status_code == 403
    got = (await client.get(_url(book_id, ch))).json()
    assert got["total"] == 1 and got["questions"][0]["question"] == MCQ["question"]


# ── Lifecycle ─────────────────────────────────────────────────────────────────

async def test_reindexing_does_not_delete_shared_questions(client):
    # Re-indexing replaces chapter rows; published questions must survive that.
    book_id, ch = await _make_chapter(client)
    await client.post(_url(book_id, ch), json={"questions": [MCQ]})

    db = await get_db()
    await db.execute("DELETE FROM chapters WHERE book_id = ?", (book_id,))
    await db.commit()

    await _switch_to_student(client)
    assert (await client.get(_url(book_id, ch))).json()["total"] == 1


async def test_deleting_book_removes_its_shared_questions(client):
    book_id, ch = await _make_chapter(client)
    await client.post(_url(book_id, ch), json={"questions": [MCQ]})
    assert (await client.delete(f"/books/{book_id}")).status_code == 204

    db = await get_db()
    async with db.execute("SELECT COUNT(*) AS n FROM shared_questions") as cur:
        assert (await cur.fetchone())["n"] == 0


# ── Chapter page per role ─────────────────────────────────────────────────────

async def test_admin_chapter_page_has_all_tabs(client):
    book_id, ch = await _make_chapter(client)
    html = (await client.get(f"/ui/books/{book_id}/chapters/{ch}")).text
    assert "switchTab('generate'" in html
    assert "switchTab('shared'" in html
    assert 'onclick="extractQuestions()"' in html
    assert re.search(r"const IS_ADMIN\s*=\s*true\b", html)
    assert 'id="tab-generate"' in html


async def test_student_chapter_page_has_extract_shared_but_not_generate(client):
    book_id, ch = await _make_chapter(client)
    await _switch_to_student(client)
    html = (await client.get(f"/ui/books/{book_id}/chapters/{ch}")).text
    assert 'onclick="extractQuestions()"' in html     # Extract visible
    assert "switchTab('shared'" in html               # Shared list visible
    assert "switchTab('generate'" not in html         # Generate hidden
    assert 'id="tab-generate"' not in html
    assert 'id="share-all-btn"' not in html
    assert re.search(r"const IS_ADMIN\s*=\s*false\b", html)
