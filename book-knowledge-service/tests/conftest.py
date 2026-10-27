"""tests/conftest.py – shared test fixtures."""

import os
import shutil
import pytest
import pytest_asyncio

# Use a temp storage dir so tests don't touch real storage
os.environ.setdefault("STORAGE_DIR",  "/tmp/bks_test_storage")
os.environ.setdefault("DATABASE_PATH", "/tmp/bks_test_storage/test.db")

from httpx import AsyncClient, ASGITransport
from app import auth as auth_module
from app.config import settings
from app.main import app
from app.database import init_db, close_db


def _reset_auth() -> None:
    """Fresh credential files (default admin only) and no live sessions."""
    shutil.rmtree(settings.auth_dir, ignore_errors=True)
    auth_module._sessions.clear()
    auth_module.ensure_auth_files()


async def _login(ac: AsyncClient, username: str, password: str, role: str) -> None:
    r = await ac.post("/auth/login", json={"username": username, "password": password, "role": role})
    assert r.status_code == 200, r.text


@pytest_asyncio.fixture(scope="function")
async def anon_client():
    """Client with no session — every protected endpoint should answer 401."""
    _reset_auth()
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    await close_db()
    # Clean up DB file
    import pathlib
    db = pathlib.Path("/tmp/bks_test_storage/test.db")
    if db.exists():
        db.unlink()
    _reset_auth()


@pytest_asyncio.fixture(scope="function")
async def client(anon_client):
    """Client logged in as the default admin (existing tests rely on this)."""
    await _login(anon_client, auth_module.DEFAULT_ADMIN_USERNAME,
                 auth_module.DEFAULT_ADMIN_PASSWORD, "admin")
    return anon_client


@pytest_asyncio.fixture(scope="function")
async def student_client(anon_client):
    """Client logged in as student 'stu' (created via the file helper)."""
    auth_module.add_student("stu", "stupass")
    await _login(anon_client, "stu", "stupass", "student")
    return anon_client
