"""tests/test_concurrency.py – slow work must not freeze other users; sessions are shared."""

import asyncio
import sqlite3
import threading
import time

import pytest
from httpx import ASGITransport, AsyncClient

from app import ai_client, auth as auth_module
from app.config import settings
from app.main import app
from app.pdf_processor import run_pdf

pytestmark = pytest.mark.asyncio


class _SlowClient:
    """Stands in for watsonx: blocks its thread for `delay` seconds."""
    def __init__(self, delay):
        self.delay, self.active, self.peak = delay, 0, 0
        self._lock = threading.Lock()

    def generate(self, prompt, max_new_tokens=None):
        with self._lock:
            self.active += 1
            self.peak = max(self.peak, self.active)
        time.sleep(self.delay)
        with self._lock:
            self.active -= 1
        return "answer"


async def _longest_stall(coro):
    """Run `coro` while a ticker measures how long the event loop was blocked."""
    worst, last = 0.0, time.time()

    async def ticker():
        nonlocal worst, last
        while True:
            await asyncio.sleep(0.02)
            now = time.time()
            worst = max(worst, now - last - 0.02)
            last = now

    t = asyncio.create_task(ticker())
    await asyncio.sleep(0.1)
    result = await coro
    await asyncio.sleep(0.1)
    t.cancel()
    return result, worst


async def test_ai_call_does_not_block_the_event_loop():
    slow = _SlowClient(0.6)
    _, stall = await _longest_stall(ai_client.ai_generate(slow, "q"))
    assert stall < 0.25, f"event loop was blocked for {stall:.2f}s"


async def test_ai_calls_run_in_parallel_but_are_capped(monkeypatch):
    monkeypatch.setattr(ai_client, "_ai_slots", asyncio.Semaphore(2))
    slow = _SlowClient(0.3)
    t0 = time.time()
    results = await asyncio.gather(*[ai_client.ai_generate(slow, "q") for _ in range(6)])
    elapsed = time.time() - t0
    assert results == ["answer"] * 6
    assert slow.peak == 2                  # never more than the cap at once
    assert elapsed < 6 * 0.3 * 0.75        # clearly faster than one-at-a-time (1.8s)


async def test_pdf_work_does_not_block_the_event_loop():
    _, stall = await _longest_stall(run_pdf(time.sleep, 0.6))
    assert stall < 0.25, f"event loop was blocked for {stall:.2f}s"


async def test_pdf_work_is_serialised():
    # PyMuPDF is single-threaded: two jobs must never overlap.
    state = {"active": 0, "peak": 0}

    def job():
        state["active"] += 1
        state["peak"] = max(state["peak"], state["active"])
        time.sleep(0.05)
        state["active"] -= 1

    await asyncio.gather(*[run_pdf(job) for _ in range(5)])
    assert state["peak"] == 1


async def test_many_users_have_independent_sessions(anon_client):
    for i in range(5):
        auth_module.add_student(f"user{i}", "password1")

    async def login(name):
        c = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        r = await c.post("/auth/login", json={"username": name, "password": "password1", "role": "student"})
        assert r.status_code == 200
        return c

    clients = await asyncio.gather(*[login(f"user{i}") for i in range(5)])
    try:
        who = await asyncio.gather(*[c.get("/auth/me") for c in clients])
        assert [r.json()["username"] for r in who] == [f"user{i}" for i in range(5)]

        await clients[0].post("/auth/logout")               # logging one out ...
        assert (await clients[0].get("/auth/me")).status_code == 401
        assert (await clients[1].get("/auth/me")).status_code == 200   # ... leaves the others
    finally:
        await asyncio.gather(*[c.aclose() for c in clients])


async def test_sessions_are_stored_on_disk_and_hashed(client):
    token = client.cookies.get(auth_module.SESSION_COOKIE)
    assert token
    conn = sqlite3.connect(settings.auth_dir / "sessions.db")
    rows = conn.execute("SELECT token_hash, username, role FROM sessions").fetchall()
    conn.close()
    assert [(r[1], r[2]) for r in rows] == [("admin", "admin")]
    assert token not in rows[0][0] and len(rows[0][0]) == 64      # only a hash is stored


async def test_session_is_visible_to_a_second_process_view(client):
    # A different worker process has no shared memory; it only has the DB file.
    # Simulate that by looking the cookie up with nothing but the file.
    from starlette.requests import Request
    token = client.cookies.get(auth_module.SESSION_COOKIE)
    scope = {"type": "http", "headers": [(b"cookie", f"{auth_module.SESSION_COOKIE}={token}".encode())]}
    user = auth_module.current_user(Request(scope))
    assert user and user.username == "admin" and user.is_admin


async def test_expired_session_is_rejected_and_removed(client):
    conn = sqlite3.connect(settings.auth_dir / "sessions.db")
    conn.execute("UPDATE sessions SET expires = ?", (time.time() - 1,))
    conn.commit()
    conn.close()
    assert (await client.get("/auth/me")).status_code == 401
    conn = sqlite3.connect(settings.auth_dir / "sessions.db")
    assert conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0
    conn.close()
