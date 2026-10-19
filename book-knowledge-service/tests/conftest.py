"""tests/conftest.py – shared test fixtures."""

import os
import pytest
import pytest_asyncio

# Use a temp storage dir so tests don't touch real storage
os.environ.setdefault("STORAGE_DIR",  "/tmp/bks_test_storage")
os.environ.setdefault("DATABASE_PATH", "/tmp/bks_test_storage/test.db")

from httpx import AsyncClient, ASGITransport
from app.main import app
from app.database import init_db, close_db


@pytest_asyncio.fixture(scope="function")
async def client():
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
