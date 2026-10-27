"""tests/test_auth.py – authentication and role-based access control."""

import io

import pytest

from app import auth as auth_module
from app.config import settings

pytestmark = pytest.mark.asyncio

MINIMAL_PDF = (
    b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
    b"xref\n0 4\n0000000000 65535 f \n"
    b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
)


def _upload(client, name="auth-test.pdf", data=MINIMAL_PDF):
    return client.post("/books", files={"file": (name, io.BytesIO(data), "application/pdf")})


# ── Credential files ──────────────────────────────────────────────────────────

async def test_default_admin_file_created(anon_client):
    text = (settings.auth_dir / "admins.txt").read_text()
    assert f"{auth_module.DEFAULT_ADMIN_USERNAME}:{auth_module.DEFAULT_ADMIN_PASSWORD}" in text
    assert (settings.auth_dir / "students.txt").exists()


# ── Login / logout ────────────────────────────────────────────────────────────

async def test_login_admin_ok(anon_client):
    r = await anon_client.post("/auth/login", json={
        "username": "admin", "password": "adminpassword", "role": "admin"})
    assert r.status_code == 200
    assert r.json() == {"username": "admin", "role": "admin"}
    me = await anon_client.get("/auth/me")
    assert me.json()["role"] == "admin"


async def test_login_wrong_password(anon_client):
    r = await anon_client.post("/auth/login", json={
        "username": "admin", "password": "nope", "role": "admin"})
    assert r.status_code == 401


async def test_login_wrong_role(anon_client):
    # An admin's credentials must not work as a student login.
    r = await anon_client.post("/auth/login", json={
        "username": "admin", "password": "adminpassword", "role": "student"})
    assert r.status_code == 401


async def test_login_unknown_role(anon_client):
    r = await anon_client.post("/auth/login", json={
        "username": "admin", "password": "adminpassword", "role": "root"})
    assert r.status_code == 401


async def test_logout_ends_session(client):
    assert (await client.get("/auth/me")).status_code == 200
    assert (await client.post("/auth/logout")).status_code == 204
    assert (await client.get("/auth/me")).status_code == 401


async def test_password_with_colon(anon_client):
    # Only the first ':' separates user from password.
    with (settings.auth_dir / "admins.txt").open("a") as f:
        f.write("boss:pa:ss:word\n")
    r = await anon_client.post("/auth/login", json={
        "username": "boss", "password": "pa:ss:word", "role": "admin"})
    assert r.status_code == 200


# ── Unauthenticated access ────────────────────────────────────────────────────

@pytest.mark.parametrize("method,url", [
    ("GET", "/books"),
    ("GET", "/books/x"),
    ("POST", "/books/x/index"),
    ("DELETE", "/books/x"),
    ("GET", "/books/x/chapters"),
    ("GET", "/books/x/pages/1"),
    ("GET", "/books/x/search?q=abc"),
    ("GET", "/books/x/chapters/c/questions"),
    ("POST", "/books/x/chapters/c/extract"),
    ("GET", "/books/x/questions/generate?topic=t"),
    ("GET", "/jobs/x"),
    ("GET", "/books/x/export"),
    ("GET", "/auth/students"),
    ("GET", "/books/x/chapters/c/shared"),
    ("DELETE", "/shared/x"),
])
async def test_anonymous_gets_401(anon_client, method, url):
    r = await anon_client.request(method, url)
    assert r.status_code == 401


@pytest.mark.parametrize("method,url", [
    ("POST", "/books/x/ask"),
    ("POST", "/books/x/chapters/c/generate-questions"),
    ("POST", "/auth/students"),
    ("POST", "/books/x/chapters/c/shared"),
    ("PUT", "/shared/x"),
])
async def test_anonymous_gets_401_for_json_posts(anon_client, method, url):
    r = await anon_client.request(method, url, json={})
    assert r.status_code == 401


async def test_pages_redirect_to_login(anon_client):
    for url in ("/ui", "/ui/students", "/ui/books/x", "/viewer/x"):
        r = await anon_client.get(url, follow_redirects=False)
        assert r.status_code == 303, url
        assert r.headers["location"] == "/login"


async def test_login_page_and_health_are_public(anon_client):
    assert (await anon_client.get("/login")).status_code == 200
    assert (await anon_client.get("/health")).status_code == 200


# ── Student restrictions ──────────────────────────────────────────────────────

async def test_student_can_read(student_client):
    assert (await student_client.get("/books")).status_code == 200
    assert (await student_client.get("/ui")).status_code == 200


async def test_student_cannot_upload_delete_or_generate(student_client):
    assert (await _upload(student_client)).status_code == 403
    assert (await student_client.delete("/books/x")).status_code == 403
    assert (await student_client.post("/books/x/index")).status_code == 403
    assert (await student_client.get("/books/x/questions/generate?topic=t")).status_code == 403
    r = await student_client.post("/books/x/chapters/c/generate-questions", json={})
    assert r.status_code == 403


async def test_student_can_extract_and_ask(student_client):
    # Allowed through the role check — the unknown ids then fail on their own
    # merits (404 / 503 when watsonx is not configured), never 401/403.
    r = await student_client.post("/books/x/chapters/c/extract")
    assert r.status_code == 404
    r = await student_client.post("/books/x/ask", json={"question": "what is it?"})
    assert r.status_code not in (401, 403)


async def test_student_cannot_write_shared(student_client):
    body = {"questions": [{"question": "Q?"}]}
    assert (await student_client.post("/books/x/chapters/c/shared", json=body)).status_code == 403
    assert (await student_client.put("/shared/x", json={"question": "Q?"})).status_code == 403
    assert (await student_client.delete("/shared/x")).status_code == 403


async def test_student_cannot_manage_students(student_client):
    assert (await student_client.get("/auth/students")).status_code == 403
    r = await student_client.post("/auth/students", json={"username": "x", "password": "xxxx"})
    assert r.status_code == 403
    assert (await student_client.get("/ui/students")).status_code == 403


async def test_student_ui_hides_admin_controls(student_client):
    html = (await student_client.get("/ui")).text
    assert 'id="drop-zone"' not in html          # upload card
    assert "const IS_ADMIN = false" in html      # no Index/Delete buttons rendered
    assert ">Students</a>" not in html           # no link to student management
    assert "stu · student" in html


# ── Admin: student management ─────────────────────────────────────────────────

async def test_admin_adds_student_who_can_log_in(client):
    r = await client.post("/auth/students", json={"username": "alice", "password": "wonder1"})
    assert r.status_code == 201
    assert "alice:wonder1" in (settings.auth_dir / "students.txt").read_text()
    assert (await client.get("/auth/students")).json() == {"students": ["alice"], "total": 1}

    await client.post("/auth/logout")
    r = await client.post("/auth/login", json={
        "username": "alice", "password": "wonder1", "role": "student"})
    assert r.status_code == 200
    assert r.json()["role"] == "student"


async def test_add_student_duplicate_rejected(client):
    body = {"username": "bob", "password": "builder"}
    assert (await client.post("/auth/students", json=body)).status_code == 201
    assert (await client.post("/auth/students", json=body)).status_code == 409
    # Case-insensitive, and may not shadow an admin either.
    assert (await client.post("/auth/students", json={"username": "BOB", "password": "builder"})).status_code == 409
    assert (await client.post("/auth/students", json={"username": "admin", "password": "builder"})).status_code == 409


@pytest.mark.parametrize("name,password", [
    ("bad name", "goodpass"),      # space in username
    ("a:b", "goodpass"),           # colon would corrupt the file format
    ("ok", "abc"),                 # password too short
    ("ok", " padded "),            # leading/trailing whitespace
])
async def test_add_student_validation(client, name, password):
    r = await client.post("/auth/students", json={"username": name, "password": password})
    assert r.status_code == 400
    assert (await client.get("/auth/students")).json()["total"] == 0


async def test_add_student_appends_after_missing_trailing_newline(client):
    path = settings.auth_dir / "students.txt"
    path.write_text("old:oldpass")          # no trailing newline
    assert (await client.post("/auth/students", json={"username": "new", "password": "newpass"})).status_code == 201
    assert path.read_text().splitlines() == ["old:oldpass", "new:newpass"]


async def test_hand_edited_student_file_is_picked_up(anon_client):
    with (settings.auth_dir / "students.txt").open("a") as f:
        f.write("# comment\n\nzed:zedpass\n")
    r = await anon_client.post("/auth/login", json={
        "username": "zed", "password": "zedpass", "role": "student"})
    assert r.status_code == 200


# ── Admin: books ──────────────────────────────────────────────────────────────

async def test_admin_upload_then_student_sees_it(client):
    book_id = (await _upload(client)).json()["book_id"]
    await client.post("/auth/logout")

    auth_module.add_student("reader", "readpass")
    await client.post("/auth/login", json={"username": "reader", "password": "readpass", "role": "student"})
    books = (await client.get("/books")).json()
    assert [b["book_id"] for b in books["books"]] == [book_id]
    assert (await client.get(f"/books/{book_id}")).status_code == 200


async def test_admin_delete_book(client):
    book_id = (await _upload(client)).json()["book_id"]
    from app.storage import book_path
    assert book_path(book_id).exists()

    assert (await client.delete(f"/books/{book_id}")).status_code == 204
    assert (await client.get(f"/books/{book_id}")).status_code == 404
    assert not book_path(book_id).exists()
    assert (await client.get("/books")).json()["total"] == 0
    # Gone means gone: a second delete is a 404, and the same file can be re-uploaded.
    assert (await client.delete(f"/books/{book_id}")).status_code == 404
    assert (await _upload(client)).status_code == 201


async def test_delete_book_removes_chapters_pages_questions_and_fts(client):
    from app.database import get_db
    from app.indexer import rebuild_fts

    book_id = (await _upload(client)).json()["book_id"]
    db = await get_db()
    await db.execute(
        "INSERT INTO chapters (chapter_id, book_id, number, title, page_start, page_end) "
        "VALUES ('ch1', ?, 1, 'Optics', 1, 1)", (book_id,))
    await db.execute(
        "INSERT INTO pages (book_id, page_number, text, chapter_id) "
        "VALUES (?, 1, 'refraction of light through a prism', 'ch1')", (book_id,))
    await db.execute(
        "INSERT INTO questions (question_id, book_id, chapter_id, chapter_number, question_type, "
        "question_text, page_start, page_end) VALUES ('q1', ?, 'ch1', 1, 'exercise', 'Define refraction', 1, 1)",
        (book_id,))
    await db.execute(
        "INSERT INTO jobs (job_id, job_type, book_id, created_at, updated_at) "
        "VALUES ('j1', 'index', ?, 'now', 'now')", (book_id,))
    await db.commit()
    await rebuild_fts(book_id)
    assert (await client.get(f"/books/{book_id}/search?q=refraction")).json()["hits"]

    assert (await client.delete(f"/books/{book_id}")).status_code == 204

    for table in ("chapters", "pages", "questions", "jobs"):
        async with db.execute(f"SELECT COUNT(*) AS n FROM {table} WHERE book_id = ?", (book_id,)) as cur:
            assert (await cur.fetchone())["n"] == 0, table
    from app.indexer import full_text_search
    assert await full_text_search("refraction", book_id=book_id) == []


async def test_delete_removes_matching_intake_copy(client):
    from app.main import _INTAKE_DIR
    _INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    name = "zz-auth-test-intake.pdf"
    data = MINIMAL_PDF + b"\n% intake-copy-marker"
    intake = _INTAKE_DIR / name
    intake.write_bytes(data)
    try:
        book_id = (await _upload(client, name=name, data=data)).json()["book_id"]
        assert (await client.delete(f"/books/{book_id}")).status_code == 204
        assert not intake.exists()
    finally:
        intake.unlink(missing_ok=True)


async def test_delete_keeps_intake_file_with_different_content(client):
    from app.main import _INTAKE_DIR
    _INTAKE_DIR.mkdir(parents=True, exist_ok=True)
    name = "zz-auth-test-other.pdf"
    intake = _INTAKE_DIR / name
    intake.write_bytes(b"%PDF-1.4 something else entirely")
    try:
        book_id = (await _upload(client, name=name)).json()["book_id"]
        assert (await client.delete(f"/books/{book_id}")).status_code == 204
        assert intake.exists()
    finally:
        intake.unlink(missing_ok=True)


async def test_upload_with_traversal_filename_does_not_escape_intake(client):
    # Client-supplied filename must never be used as a path on delete.
    book_id = (await _upload(client, name="../../../etc/hostname")).json()["book_id"]
    assert (await client.delete(f"/books/{book_id}")).status_code == 204


# ── Admin pages ───────────────────────────────────────────────────────────────

async def test_admin_pages_render(client):
    html = (await client.get("/ui")).text
    assert 'id="drop-zone"' in html
    assert "const IS_ADMIN = true" in html
    assert ">Students</a>" in html
    assert "Add a student" in (await client.get("/ui/students")).text


async def test_login_page_redirects_when_signed_in(client):
    r = await client.get("/login", follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/ui"
