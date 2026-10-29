"""tests/test_tasks.py – assigning shared questions to students, My Tasks, export."""

import io

import pytest

from app import auth as auth_module
from app.database import get_db
from app.models import ChapterRecord, ExportFormat, QuestionRecord, QuestionType
from app.exporter import export

pytestmark = pytest.mark.asyncio

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
)


async def _make_chapter(client, chapter_id="ch1"):
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


async def _login(client, name, password, role):
    await client.post("/auth/logout")
    r = await client.post("/auth/login", json={"username": name, "password": password, "role": role})
    assert r.status_code == 200


async def _as_student(client, name):
    await _login(client, name, name + "pass", "student")


async def _as_admin(client):
    await _login(client, auth_module.DEFAULT_ADMIN_USERNAME, auth_module.DEFAULT_ADMIN_PASSWORD, "admin")


@pytest.fixture
def three_students():
    for n in ("alice", "bob", "carol"):
        auth_module.add_student(n, n + "pass")


# ── Assignment ────────────────────────────────────────────────────────────────

async def test_share_to_all_is_visible_to_every_student(client, three_students):
    book_id, ch = await _make_chapter(client)
    r = await client.post(_url(book_id, ch), json={"questions": [{"question": "For everyone?"}]})
    assert r.status_code == 201
    assert r.json()["questions"][0]["assigned_to"] == []
    for name in ("alice", "bob", "carol"):
        await _as_student(client, name)
        assert (await client.get(_url(book_id, ch))).json()["total"] == 1


async def test_share_to_selected_students_only(client, three_students):
    book_id, ch = await _make_chapter(client)
    r = await client.post(_url(book_id, ch), json={
        "questions": [{"question": "Just for two"}], "students": ["bob", "alice"]})
    assert r.status_code == 201
    assert r.json()["questions"][0]["assigned_to"] == ["alice", "bob"]

    await _as_student(client, "alice")
    assert (await client.get(_url(book_id, ch))).json()["total"] == 1
    await _as_student(client, "bob")
    assert (await client.get(_url(book_id, ch))).json()["total"] == 1
    await _as_student(client, "carol")
    assert (await client.get(_url(book_id, ch))).json()["total"] == 0

    await _as_admin(client)                       # admin always sees everything
    assert (await client.get(_url(book_id, ch))).json()["total"] == 1


async def test_share_to_unknown_student_is_rejected(client, three_students):
    book_id, ch = await _make_chapter(client)
    r = await client.post(_url(book_id, ch), json={"questions": [{"question": "Q?"}], "students": ["alice", "ghost"]})
    assert r.status_code == 400
    assert "ghost" in r.json()["detail"]
    assert (await client.get(_url(book_id, ch))).json()["total"] == 0   # nothing was stored


async def test_empty_student_list_is_rejected(client, three_students):
    book_id, ch = await _make_chapter(client)
    r = await client.post(_url(book_id, ch), json={"questions": [{"question": "Q?"}], "students": []})
    assert r.status_code == 422


async def test_unshare_removes_assignment_rows(client, three_students):
    book_id, ch = await _make_chapter(client)
    sid = (await client.post(_url(book_id, ch), json={
        "questions": [{"question": "Q?"}], "students": ["alice"]})).json()["questions"][0]["share_id"]
    assert (await client.delete(f"/shared/{sid}")).status_code == 204
    db = await get_db()
    async with db.execute("SELECT COUNT(*) AS n FROM shared_question_assignees") as cur:
        assert (await cur.fetchone())["n"] == 0


async def test_edit_keeps_assignment(client, three_students):
    book_id, ch = await _make_chapter(client)
    sid = (await client.post(_url(book_id, ch), json={
        "questions": [{"question": "Old"}], "students": ["carol"]})).json()["questions"][0]["share_id"]
    r = await client.put(f"/shared/{sid}", json={"question": "New"})
    assert r.status_code == 200 and r.json()["assigned_to"] == ["carol"]


# ── GET /tasks ────────────────────────────────────────────────────────────────

async def test_student_tasks_lists_only_their_assignments(client, three_students):
    book_id, ch = await _make_chapter(client)
    await client.post(_url(book_id, ch), json={"questions": [{"question": "to alice"}], "students": ["alice"]})
    await client.post(_url(book_id, ch), json={"questions": [{"question": "to all"}]})
    await client.post(_url(book_id, ch), json={"questions": [{"question": "to bob"}], "students": ["bob"]})

    await _as_student(client, "alice")
    d = (await client.get("/tasks")).json()
    assert d["total"] == 2
    assert {t["question"] for t in d["tasks"]} == {"to alice", "to all"}
    t = d["tasks"][0]
    assert t["book_id"] == book_id and t["chapter_id"] == ch
    assert t["chapter_title"] == "Mechanics" and t["chapter_number"] == 1

    await _as_student(client, "carol")
    assert {t["question"] for t in (await client.get("/tasks")).json()["tasks"]} == {"to all"}


async def test_admin_tasks_lists_everything(client, three_students):
    book_id, ch = await _make_chapter(client)
    await client.post(_url(book_id, ch), json={"questions": [{"question": "a"}], "students": ["alice"]})
    await client.post(_url(book_id, ch), json={"questions": [{"question": "b"}]})
    assert (await client.get("/tasks")).json()["total"] == 2


async def test_tasks_requires_login(anon_client):
    assert (await anon_client.get("/tasks")).status_code == 401


# ── DELETE /tasks (clear) ─────────────────────────────────────────────────────

async def _two_chapters(client):
    book_id, ch1 = await _make_chapter(client, "ch1")
    db = await get_db()
    await db.execute(
        "INSERT INTO chapters (chapter_id, book_id, number, title, page_start, page_end) "
        "VALUES ('ch2', ?, 2, 'Heat', 1, 1)", (book_id,))
    await db.commit()
    await client.post(_url(book_id, "ch1"), json={"questions": [{"question": "a"}, {"question": "b"}], "students": ["alice"]})
    await client.post(_url(book_id, "ch2"), json={"questions": [{"question": "c"}]})
    return book_id


async def test_clear_all_tasks(client, three_students):
    await _two_chapters(client)
    r = await client.delete("/tasks")
    assert r.status_code == 200 and r.json() == {"deleted": 3}
    assert (await client.get("/tasks")).json()["total"] == 0
    db = await get_db()
    async with db.execute("SELECT COUNT(*) AS n FROM shared_question_assignees") as cur:
        assert (await cur.fetchone())["n"] == 0


async def test_clear_tasks_of_one_chapter(client, three_students):
    book_id = await _two_chapters(client)
    r = await client.delete("/tasks", params={"book_id": book_id, "chapter_id": "ch1"})
    assert r.json() == {"deleted": 2}
    assert [t["question"] for t in (await client.get("/tasks")).json()["tasks"]] == ["c"]


async def test_clear_tasks_is_admin_only(client, three_students):
    await _two_chapters(client)
    await _as_student(client, "alice")
    assert (await client.delete("/tasks")).status_code == 403
    await _as_admin(client)
    assert (await client.get("/tasks")).json()["total"] == 3


async def test_tasks_page_has_clear_buttons_for_admin_only(client, three_students):
    assert 'id="clear-all"' in (await client.get("/ui/tasks")).text
    await _as_student(client, "alice")
    assert 'id="clear-all"' not in (await client.get("/ui/tasks")).text



# ── Pages ─────────────────────────────────────────────────────────────────────

async def test_tasks_page_for_student_and_anonymous(anon_client):
    r = await anon_client.get("/ui/tasks", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == "/login"
    auth_module.add_student("pupil", "pupilpass")
    await _login(anon_client, "pupil", "pupilpass", "student")
    html = (await anon_client.get("/ui/tasks")).text
    assert "My Tasks" in html


async def test_every_page_has_back_and_tasks_links(client):
    book_id, ch = await _make_chapter(client)
    for url in ("/ui/tasks", "/ui/students", f"/ui/books/{book_id}", f"/ui/books/{book_id}/chapters/{ch}"):
        html = (await client.get(url)).text
        assert 'id="back-link"' in html, url
        assert 'href="/ui/tasks"' in html, url
    assert f'href="/ui/books/{book_id}"' in (await client.get(f"/viewer/{book_id}")).text   # reader back link


async def test_chapter_page_has_student_picker_for_admin_only(client, three_students):
    book_id, ch = await _make_chapter(client)
    assert 'id="student-picks"' in (await client.get(f"/ui/books/{book_id}/chapters/{ch}")).text
    await _as_student(client, "alice")
    assert 'id="student-picks"' not in (await client.get(f"/ui/books/{book_id}/chapters/{ch}")).text


# ── Export / download ─────────────────────────────────────────────────────────

def _q(text, ch_id="c1"):
    return QuestionRecord(
        question_id="q" + text[:3], book_id="b", chapter_id=ch_id, chapter_number=1,
        question_type=QuestionType.objective_1, question_number="3", question_text=text,
        solution_text="so a < b & c > d", answer_text="<b>", page_start=1, page_end=1)


async def test_pdf_export_survives_angle_brackets_and_ampersands():
    ch = ChapterRecord(chapter_id="c1", book_id="b", number=1, title="A < B &\nC", page_start=1, page_end=1)
    data, mt = export(ExportFormat.pdf, [_q("If a <13 and A>B then x & y (a <b)")], [ch], "Book <1> & co", True)
    assert mt == "application/pdf" and data.startswith(b"%PDF")


async def test_book_page_has_download_all(client):
    book_id, _ = await _make_chapter(client)
    html = (await client.get(f"/ui/books/{book_id}")).text
    assert "downloadAll()" in html and 'id="dl-fmt"' in html


async def test_extract_job_reports_failure_instead_of_hanging(client, monkeypatch):
    import asyncio
    from app.routers import questions as qmod
    book_id, ch = await _make_chapter(client)
    db = await get_db()
    await db.execute("UPDATE books SET status='indexed' WHERE book_id=?", (book_id,))
    await db.commit()
    monkeypatch.setattr(qmod, "extract_questions_from_chapter",
                        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")))
    job_id = (await client.post(f"/books/{book_id}/chapters/{ch}/extract")).json()["job_id"]
    for _ in range(20):
        await asyncio.sleep(0.05)
        j = (await client.get(f"/jobs/{job_id}")).json()
        if j["status"] != "pending":
            break
    assert j["status"] == "failed" and "boom" in j["error"]
