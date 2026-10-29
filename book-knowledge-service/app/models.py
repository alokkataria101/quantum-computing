"""app/models.py – Pydantic schemas for API request/response and internal data."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Optional

from pydantic import BaseModel, Field, StringConstraints


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
    compile_pdf = "compile_pdf"


class CompileMode(str, Enum):
    questions = "questions"
    notes     = "notes"
    both      = "both"


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
    source: str = "toc"               # "toc" | "contents" | "inferred"

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


# ── Generate ──────────────────────────────────────────────────────────────────

class GenerateResult(BaseModel):
    questions: list[QuestionRecord]
    total: int
    topic: str
    question_type: QuestionType
    random: bool


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


# ── AI / watsonx ──────────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str = Field(..., min_length=5, description="Question to ask about the book")
    chapter_id: Optional[str] = Field(None, description="Restrict search to this chapter (omit to search the whole book)")
    max_pages: int = Field(5, ge=1, le=20, description="Max pages to include as context")


class AskSource(BaseModel):
    page_number: int
    chapter_id: Optional[str] = None
    chapter_number: Optional[int] = None
    chapter_title: Optional[str] = None


class AskResponse(BaseModel):
    question: str
    answer: str
    source_pages: list[int]
    sources: list[AskSource] = []          # where the answer came from (best match first)
    chapter_title: Optional[str] = None
    ai_enabled: bool


class GenerateQuestionsRequest(BaseModel):
    chapter_id: Optional[str] = Field(None, description="Chapter to generate questions from (optional — taken from URL path when using /chapters/{id}/generate-questions)")
    question_type: str = Field(
        "mixed",
        description=(
            "Type of questions: 'mcq' (multiple choice), 'short' (short answer), "
            "'numerical' (numerical problems), 'mixed' (all types)"
        ),
    )
    count: int = Field(5, ge=1, le=20, description="Number of questions to generate")
    difficulty: str = Field(
        "medium",
        description="Difficulty level: 'easy', 'medium', 'hard'",
    )


class GeneratedQuestion(BaseModel):
    number: int
    type: str                          # mcq | short | numerical
    question: str                      # full question text with proper notation
    options: Optional[list[str]] = None  # A, B, C, D for MCQ
    answer: Optional[str] = None
    hint: Optional[str] = None
    page_start: Optional[int] = None   # source page number (for thumbnail)


class GenerateQuestionsResponse(BaseModel):
    chapter_title: str
    chapter_number: int
    questions: list[GeneratedQuestion]
    total: int
    ai_enabled: bool
    note: Optional[str] = None         # shown when AI is disabled


# ── Shared (admin-curated) questions ──────────────────────────────────────────

class SharedQuestionIn(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=5000)]
    type: str = Field("question", max_length=32)
    options: Optional[list[Annotated[str, StringConstraints(max_length=1000)]]] = Field(None, max_length=10)
    answer: Optional[str] = Field(None, max_length=5000)
    hint: Optional[str] = Field(None, max_length=2000)
    page_start: Optional[int] = Field(None, ge=1)


class SharedQuestionsCreate(BaseModel):
    questions: list[SharedQuestionIn] = Field(..., min_length=1, max_length=100)
    # Students who get the questions. Omitted/null = every student.
    students: Optional[list[str]] = Field(None, min_length=1, max_length=1000)


class SharedQuestion(SharedQuestionIn):
    share_id: str
    book_id: str
    chapter_id: str
    shared_by: str
    shared_at: datetime
    updated_at: datetime
    assigned_to: list[str] = []            # empty = every student


class SharedQuestionList(BaseModel):
    questions: list[SharedQuestion]
    total: int


class AssignedTask(SharedQuestion):
    book_title: Optional[str] = None
    chapter_number: Optional[int] = None
    chapter_title: Optional[str] = None


class AssignedTaskList(BaseModel):
    tasks: list[AssignedTask]
    total: int


# ── Shared compiled PDFs ──────────────────────────────────────────────────────

class CompiledPdf(BaseModel):
    compile_id: str
    book_id: str
    job_id: str
    mode: str
    label: str
    chapters_desc: str
    page_count: int
    created_by: str
    created_at: datetime
    book_title: Optional[str] = None
    is_shared: bool = False          # True if at least one shared_pdfs row points here


class CompiledPdfList(BaseModel):
    pdfs: list[CompiledPdf]
    total: int


class SharePdfRequest(BaseModel):
    label: str = Field("", max_length=200, description="Optional display label for students.")
    students: Optional[list[str]] = Field(
        None, description="Specific student usernames. Omit or null = all students."
    )


class SharedPdf(BaseModel):
    share_id: str
    book_id: str
    job_id: str
    mode: str
    label: str
    shared_by: str
    shared_at: datetime
    assigned_to: list[str] = []   # empty = every student
    book_title: Optional[str] = None


class SharedPdfList(BaseModel):
    pdfs: list[SharedPdf]
    total: int
