"""app/models.py – Pydantic schemas for API request/response and internal data."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ── Enums ─────────────────────────────────────────────────────────────────────

class BookStatus(str, Enum):
    uploaded   = "uploaded"
    indexing   = "indexing"
    indexed    = "indexed"
    error      = "error"


class JobStatus(str, Enum):
    pending    = "pending"
    running    = "running"
    done       = "done"
    failed     = "failed"
    cancelled  = "cancelled"


class JobType(str, Enum):
    index      = "index"
    extract    = "extract"


class QuestionType(str, Enum):
    example        = "example"
    solved_example = "solved_example"
    exercise       = "exercise"
    short_answer   = "short_answer"
    objective_1    = "objective_1"
    objective_2    = "objective_2"
    worked_example = "worked_example"
    other          = "other"


class ExportFormat(str, Enum):
    html = "html"
    json = "json"
    csv  = "csv"
    pdf  = "pdf"


# ── Book ──────────────────────────────────────────────────────────────────────

class BookBase(BaseModel):
    title: str
    author: str = ""
    total_pages: int = 0


class BookCreate(BookBase):
    pass


class BookRecord(BookBase):
    book_id: str
    filename: str
    sha256: str
    file_size: int
    status: BookStatus
    created_at: datetime
    indexed_at: Optional[datetime] = None
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class BookList(BaseModel):
    books: list[BookRecord]
    total: int


# ── Chapter ───────────────────────────────────────────────────────────────────

class ChapterRecord(BaseModel):
    chapter_id: str
    book_id: str
    number: int                       # 0 = front matter
    title: str
    page_start: int
    page_end: int
    confidence: float = 1.0           # 0.0–1.0 detection confidence
    source: str = "toc"               # "toc" | "inferred"

    model_config = {"from_attributes": True}


class ChapterList(BaseModel):
    chapters: list[ChapterRecord]


# ── Page ──────────────────────────────────────────────────────────────────────

class PageRecord(BaseModel):
    book_id: str
    page_number: int                  # 1-based, matches PDF page
    text: str
    has_images: bool = False
    is_scanned: bool = False
    ocr_used: bool = False
    chapter_id: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Question / Example ────────────────────────────────────────────────────────

class QuestionRecord(BaseModel):
    question_id: str
    book_id: str
    chapter_id: str
    chapter_number: int
    question_type: QuestionType
    question_number: Optional[str] = None   # e.g. "1.2", "A", "iii"
    question_text: str
    solution_text: Optional[str] = None
    answer_text: Optional[str] = None
    page_start: int
    page_end: int
    confidence: float = 1.0
    extraction_method: str = "pattern"      # "pattern" | "llm"

    model_config = {"from_attributes": True}


class QuestionList(BaseModel):
    questions: list[QuestionRecord]
    total: int
    chapter_id: str


# ── Job ───────────────────────────────────────────────────────────────────────

class JobRecord(BaseModel):
    job_id: str
    job_type: JobType
    book_id: str
    chapter_id: Optional[str] = None
    status: JobStatus
    progress: float = 0.0             # 0.0–1.0
    message: str = ""
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── Search ────────────────────────────────────────────────────────────────────

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    book_id: Optional[str] = None
    chapter_id: Optional[str] = None
    page_start: Optional[int] = None
    page_end: Optional[int] = None
    limit: int = Field(20, ge=1, le=100)


class SearchHit(BaseModel):
    book_id: str
    page_number: int
    chapter_id: Optional[str]
    snippet: str
    score: float


class SearchResult(BaseModel):
    hits: list[SearchHit]
    total: int
    query: str


# ── Export ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    fmt: ExportFormat = ExportFormat.json
    chapter_ids: Optional[list[str]] = None   # None = all chapters
    question_types: Optional[list[QuestionType]] = None
    include_solutions: bool = True
