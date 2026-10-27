"""app/auth.py – plain-text credential files, shared (SQLite) sessions, FastAPI guards.

Credentials live in two local text files (one ``username:password`` per line,
``#`` comments and blank lines ignored):

    <STORAGE_DIR>/auth/admins.txt
    <STORAGE_DIR>/auth/students.txt

The files are re-read on every login, so they can be edited by hand without a
restart.  Passwords are stored in plain text by design (local/prototype use).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import sqlite3
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends, HTTPException, Request

from .config import settings

logger = logging.getLogger(__name__)

SESSION_COOKIE = "bks_session"
SESSION_TTL_SECONDS = 12 * 60 * 60

ROLE_ADMIN = "admin"
ROLE_STUDENT = "student"
ROLES = (ROLE_ADMIN, ROLE_STUDENT)

# Seeded into admins.txt the first time the service starts. Change it there.
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "adminpassword"

_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,32}$")
_write_lock = threading.Lock()


class DuplicateUserError(ValueError):
    """Username already exists (as admin or student)."""


@dataclass(frozen=True)
class User:
    username: str
    role: str

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN


# ── Credential files ─────────────────────────────────────────────────────────

def _admins_file() -> Path:
    return settings.auth_dir / "admins.txt"


def _students_file() -> Path:
    return settings.auth_dir / "students.txt"


def ensure_auth_files() -> None:
    """Create the auth folder and credential files if they do not exist yet."""
    settings.auth_dir.mkdir(parents=True, exist_ok=True)
    admins, students = _admins_file(), _students_file()
    if not admins.exists():
        admins.write_text(
            "# admin credentials — one username:password per line\n"
            f"{DEFAULT_ADMIN_USERNAME}:{DEFAULT_ADMIN_PASSWORD}\n",
            encoding="utf-8",
        )
        logger.warning(
            "Created %s with default admin '%s' — change the password.",
            admins, DEFAULT_ADMIN_USERNAME,
        )
    if not students.exists():
        students.write_text(
            "# student credentials — one username:password per line\n",
            encoding="utf-8",
        )
    for f in (admins, students):
        try:
            os.chmod(f, 0o600)
        except OSError:
            pass


def _read_credentials(path: Path) -> dict[str, str]:
    creds: dict[str, str] = {}
    if not path.exists():
        return creds
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, sep, password = line.partition(":")
        name = name.strip()
        if sep and name:
            creds[name] = password
    return creds


def authenticate(username: str, password: str, role: str) -> bool:
    """True if ``username``/``password`` match an entry in the file for ``role``."""
    if role not in ROLES:
        return False
    ensure_auth_files()
    path = _admins_file() if role == ROLE_ADMIN else _students_file()
    stored = _read_credentials(path).get(username)
    # Compare even when the user is unknown so timing does not reveal usernames.
    ok = hmac.compare_digest((stored or "").encode(), password.encode())
    return stored is not None and ok


def list_students() -> list[str]:
    ensure_auth_files()
    return sorted(_read_credentials(_students_file()))


def add_student(username: str, password: str) -> None:
    """Append a student to students.txt. Raises ValueError / DuplicateUserError."""
    if not _USERNAME_RE.match(username):
        raise ValueError(
            "Username must be 1-32 characters: letters, digits, '_', '.' or '-'."
        )
    if not (4 <= len(password) <= 128):
        raise ValueError("Password must be 4-128 characters.")
    if password != password.strip() or any(ord(c) < 32 for c in password):
        raise ValueError(
            "Password must not start/end with whitespace or contain control characters."
        )

    with _write_lock:
        ensure_auth_files()
        taken = {
            n.lower()
            for n in (*_read_credentials(_admins_file()),
                      *_read_credentials(_students_file()))
        }
        if username.lower() in taken:
            raise DuplicateUserError(f"User '{username}' already exists.")
        path = _students_file()
        text = path.read_text(encoding="utf-8")
        prefix = "" if (not text or text.endswith("\n")) else "\n"
        with path.open("a", encoding="utf-8") as f:
            f.write(f"{prefix}{username}:{password}\n")
    logger.info("Student '%s' added.", username)


# ── Sessions ─────────────────────────────────────────────────────────────────
# Stored in a small SQLite file (<STORAGE_DIR>/auth/sessions.db) rather than in
# process memory, so every uvicorn worker sees the same logins and sessions
# survive a restart. Only a hash of the token is stored.

def _session_conn() -> sqlite3.Connection:
    settings.auth_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.auth_dir / "sessions.db", timeout=10)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS sessions ("
        " token_hash TEXT PRIMARY KEY, username TEXT NOT NULL,"
        " role TEXT NOT NULL, expires REAL NOT NULL)"
    )
    return conn


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(user: User) -> str:
    token = secrets.token_urlsafe(32)
    now = time.time()
    conn = _session_conn()
    try:
        with conn:
            conn.execute("DELETE FROM sessions WHERE expires < ?", (now,))
            conn.execute(
                "INSERT INTO sessions VALUES (?,?,?,?)",
                (_hash_token(token), user.username, user.role, now + SESSION_TTL_SECONDS),
            )
    finally:
        conn.close()
    return token


def destroy_session(token: str | None) -> None:
    if not token:
        return
    conn = _session_conn()
    try:
        with conn:
            conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
    finally:
        conn.close()


def clear_sessions() -> None:
    conn = _session_conn()
    try:
        with conn:
            conn.execute("DELETE FROM sessions")
    finally:
        conn.close()


def current_user(request: Request) -> User | None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        return None
    conn = _session_conn()
    try:
        row = conn.execute(
            "SELECT username, role, expires FROM sessions WHERE token_hash = ?",
            (_hash_token(token),),
        ).fetchone()
        if not row:
            return None
        if row[2] < time.time():
            with conn:
                conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_hash_token(token),))
            return None
        return User(username=row[0], role=row[1])
    finally:
        conn.close()


# ── FastAPI dependencies ─────────────────────────────────────────────────────

async def require_user(request: Request) -> User:
    """API guard: any logged-in user, else 401."""
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated. Log in at /login.")
    return user


async def require_admin(user: User = Depends(require_user)) -> User:
    """API guard: admin only, else 403."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


async def page_user(request: Request) -> User:
    """HTML page guard: not logged in → 303 redirect to /login."""
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=303, headers={"Location": "/login"})
    return user


async def page_admin(user: User = Depends(page_user)) -> User:
    """HTML page guard: admin only, else 403."""
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user
