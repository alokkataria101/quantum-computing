"""tests/test_ask.py – Ask AI searches the whole book and reports its sources."""

import io

import pytest

from app import indexer
from app.database import get_db
from app.routers import ai as ai_router

pytestmark = pytest.mark.asyncio

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
)


class FakeAI:
    def __init__(self):
        self.prompts = []

    def is_enabled(self):
        return True

    def generate(self, prompt, max_new_tokens=None):
        self.prompts.append(prompt)
        return "Fake answer"


@pytest.fixture
def fake_ai(monkeypatch):
    fake = FakeAI()
    monkeypatch.setattr(ai_router, "get_ai_client", lambda: fake)
    return fake


async def _book_with_two_chapters(client):
    r = await client.post("/books", files={"file": ("s.pdf", io.BytesIO(MINIMAL_PDF), "application/pdf")})
    book_id = r.json()["book_id"]
    db = await get_db()
    await db.execute("UPDATE books SET status='indexed' WHERE book_id=?", (book_id,))
    for cid, num, title, pg in (("c1", 1, "Fluids", 1), ("c2", 2, "Heat", 2)):
        await db.execute(
            "INSERT INTO chapters (chapter_id, book_id, number, title, page_start, page_end) "
            "VALUES (?,?,?,?,?,?)", (cid, book_id, num, title, pg, pg))
    texts = {1: ("c1", "Pascal pressure law applies to fluids at rest."),
             2: ("c2", "Pascal also appears in heat engines through pressure cycles.")}
    for pg, (cid, text) in texts.items():
        await db.execute(
            "INSERT OR REPLACE INTO pages (book_id, page_number, text, chapter_id) VALUES (?,?,?,?)",
            (book_id, pg, text, cid))
    await db.commit()
    await indexer.rebuild_fts(book_id)
    return book_id


async def test_ask_without_chapter_searches_whole_book(client, fake_ai):
    book_id = await _book_with_two_chapters(client)
    r = await client.post(f"/books/{book_id}/ask", json={"question": "Pascal pressure"})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"] == "Fake answer"
    assert {s["chapter_id"] for s in body["sources"]} == {"c1", "c2"}
    by_chapter = {s["chapter_id"]: s for s in body["sources"]}
    assert by_chapter["c2"]["chapter_number"] == 2
    assert by_chapter["c2"]["chapter_title"] == "Heat"
    assert by_chapter["c2"]["page_number"] == 2
    assert "Chapter 1: Fluids" in fake_ai.prompts[0]
    assert "Chapter 2: Heat" in fake_ai.prompts[0]


async def test_ask_with_chapter_restricts_results(client, fake_ai):
    book_id = await _book_with_two_chapters(client)
    r = await client.post(f"/books/{book_id}/ask",
                          json={"question": "Pascal pressure", "chapter_id": "c1"})
    assert r.status_code == 200, r.text
    assert {s["chapter_id"] for s in r.json()["sources"]} == {"c1"}


async def test_student_can_ask_whole_book(student_client, fake_ai):
    # create the book as admin, then ask as the student
    from tests.conftest import _login
    from app import auth as auth_module
    await student_client.post("/auth/logout")
    await _login(student_client, auth_module.DEFAULT_ADMIN_USERNAME,
                 auth_module.DEFAULT_ADMIN_PASSWORD, "admin")
    book_id = await _book_with_two_chapters(student_client)
    await student_client.post("/auth/logout")
    await _login(student_client, "stu", "stupass", "student")
    r = await student_client.post(f"/books/{book_id}/ask", json={"question": "Pascal pressure"})
    assert r.status_code == 200, r.text
    assert len(r.json()["sources"]) == 2


async def test_chapter_page_offers_whole_book_scope(client):
    book_id = await _book_with_two_chapters(client)
    html = (await client.get(f"/ui/books/{book_id}/chapters/c1")).text
    assert 'id="ask-scope"' in html
    assert "Whole book" in html
    assert "This chapter only" in html
