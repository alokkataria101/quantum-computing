"""app/storage.py – PDF file storage with hash-based deduplication."""

from __future__ import annotations

import hashlib
import io
import logging
import shutil
from pathlib import Path

import aiofiles

from .config import settings

logger = logging.getLogger(__name__)


def _ensure_dirs() -> None:
    settings.books_dir.mkdir(parents=True, exist_ok=True)
    settings.indexes_dir.mkdir(parents=True, exist_ok=True)
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    crops_dir().mkdir(parents=True, exist_ok=True)


def crops_dir() -> Path:
    d = settings.storage_dir / "crops"
    d.mkdir(parents=True, exist_ok=True)
    return d


def question_crop_path(question_id: str) -> Path:
    return crops_dir() / f"{question_id}.png"


def book_path(book_id: str) -> Path:
    return settings.books_dir / f"{book_id}.pdf"


def export_path(filename: str) -> Path:
    settings.exports_dir.mkdir(parents=True, exist_ok=True)
    return settings.exports_dir / filename


def render_cache_dir(book_id: str) -> Path:
    d = settings.indexes_dir / book_id / "renders"
    d.mkdir(parents=True, exist_ok=True)
    return d


def rendered_page_path(book_id: str, page_number: int) -> Path:
    return render_cache_dir(book_id) / f"page_{page_number:05d}.png"


async def save_uploaded_pdf(data: bytes, book_id: str) -> tuple[str, int]:
    """
    Write PDF bytes to storage.
    Returns (sha256_hex, file_size).
    """
    _ensure_dirs()
    sha256 = hashlib.sha256(data).hexdigest()
    dest = book_path(book_id)
    async with aiofiles.open(dest, "wb") as f:
        await f.write(data)
    logger.info("Saved %d bytes for book %s → %s", len(data), book_id, dest)
    return sha256, len(data)


def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def delete_book_files(book_id: str) -> None:
    p = book_path(book_id)
    if p.exists():
        p.unlink()
    cache = settings.indexes_dir / book_id
    if cache.exists():
        shutil.rmtree(cache)
    logger.info("Deleted files for book %s", book_id)


def validate_pdf_bytes(data: bytes, max_bytes: int) -> None:
    """Raise ValueError for invalid or oversized uploads."""
    if len(data) > max_bytes:
        raise ValueError(f"File exceeds maximum allowed size of {max_bytes // (1024*1024)} MB.")
    if not data.startswith(b"%PDF"):
        raise ValueError("Uploaded file does not appear to be a valid PDF (missing %PDF header).")
