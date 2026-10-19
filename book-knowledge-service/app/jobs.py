"""app/jobs.py – async in-process background job runner."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Coroutine, Optional

import aiosqlite

from .database import get_db

logger = logging.getLogger(__name__)

_active_tasks: dict[str, asyncio.Task] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def create_job(
    job_type: str,
    book_id: str,
    chapter_id: Optional[str] = None,
) -> str:
    job_id = str(uuid.uuid4())
    db = await get_db()
    now = _now()
    await db.execute(
        """INSERT INTO jobs (job_id, job_type, book_id, chapter_id, status,
                             progress, message, created_at, updated_at)
           VALUES (?,?,?,?,'pending',0.0,'',?,?)""",
        (job_id, job_type, book_id, chapter_id, now, now),
    )
    await db.commit()
    return job_id


async def update_job(
    job_id: str,
    status: str | None = None,
    progress: float | None = None,
    message: str | None = None,
    error: str | None = None,
) -> None:
    db = await get_db()
    fields: list[str] = ["updated_at = ?"]
    params: list = [_now()]
    if status is not None:
        fields.append("status = ?"); params.append(status)
    if progress is not None:
        fields.append("progress = ?"); params.append(progress)
    if message is not None:
        fields.append("message = ?"); params.append(message)
    if error is not None:
        fields.append("error = ?"); params.append(error)
    params.append(job_id)
    await db.execute(f"UPDATE jobs SET {', '.join(fields)} WHERE job_id = ?", params)
    await db.commit()


async def get_job(job_id: str) -> Optional[dict]:
    db = await get_db()
    async with db.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)) as cur:
        row = await cur.fetchone()
    return dict(row) if row else None


async def run_job(
    job_id: str,
    coro_factory: Callable[[], Coroutine],
) -> None:
    """
    Run an async coroutine as a tracked background task.
    Updates job status automatically on start, completion, and failure.
    """
    await update_job(job_id, status="running", progress=0.0, message="Starting…")

    async def _wrapper():
        try:
            await coro_factory()
            await update_job(job_id, status="done", progress=1.0, message="Completed.")
        except asyncio.CancelledError:
            await update_job(job_id, status="cancelled", message="Cancelled by user.")
        except Exception as exc:
            logger.exception("Job %s failed: %s", job_id, exc)
            await update_job(
                job_id, status="failed", error=str(exc), message="Job failed."
            )
        finally:
            _active_tasks.pop(job_id, None)

    task = asyncio.create_task(_wrapper())
    _active_tasks[job_id] = task


async def cancel_job(job_id: str) -> bool:
    task = _active_tasks.get(job_id)
    if task and not task.done():
        task.cancel()
        return True
    return False
