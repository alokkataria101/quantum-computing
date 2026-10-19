"""tests/test_api.py – integration tests for the FastAPI endpoints."""

import io
import pytest
import pytest_asyncio

pytestmark = pytest.mark.asyncio


# ── Health ────────────────────────────────────────────────────────────────────

async def test_health(client):
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_root(client):
    r = await client.get("/")
    assert r.status_code == 200
    assert "book-knowledge-service" in r.json()["service"]


# ── Book list (empty) ─────────────────────────────────────────────────────────

async def test_list_books_empty(client):
    r = await client.get("/books")
    assert r.status_code == 200
    assert r.json()["total"] == 0


# ── Upload validation ─────────────────────────────────────────────────────────

async def test_upload_invalid_not_pdf(client):
    fake = io.BytesIO(b"This is not a PDF file at all")
    r = await client.post("/books", files={"file": ("test.pdf", fake, "application/pdf")})
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]


async def test_upload_valid_minimal_pdf(client):
    # Minimal valid PDF
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )
    f = io.BytesIO(minimal_pdf)
    r = await client.post("/books", files={"file": ("hcv.pdf", f, "application/pdf")})
    assert r.status_code == 201
    data = r.json()
    assert "book_id" in data
    assert data["status"] == "uploaded"
    return data["book_id"]


async def test_upload_duplicate_rejected(client):
    minimal_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R>>endobj\n"
        b"xref\n0 4\n0000000000 65535 f \n"
        b"trailer<</Size 4/Root 1 0 R>>\nstartxref\n0\n%%EOF"
    )
    f1 = io.BytesIO(minimal_pdf)
    r1 = await client.post("/books", files={"file": ("dup.pdf", f1, "application/pdf")})
    assert r1.status_code == 201

    f2 = io.BytesIO(minimal_pdf)
    r2 = await client.post("/books", files={"file": ("dup.pdf", f2, "application/pdf")})
    assert r2.status_code == 409


async def test_get_nonexistent_book(client):
    r = await client.get("/books/nonexistent-id")
    assert r.status_code == 404


async def test_get_nonexistent_job(client):
    r = await client.get("/jobs/nonexistent-job-id")
    assert r.status_code == 404


# ── Storage helpers ───────────────────────────────────────────────────────────

def test_validate_pdf_bytes_header():
    from app.storage import validate_pdf_bytes
    validate_pdf_bytes(b"%PDF-1.4 valid", max_bytes=1024 * 1024)


def test_validate_pdf_bytes_bad_header():
    from app.storage import validate_pdf_bytes
    import pytest
    with pytest.raises(ValueError, match="PDF"):
        validate_pdf_bytes(b"Not a PDF", max_bytes=1024 * 1024)


def test_validate_pdf_bytes_too_large():
    from app.storage import validate_pdf_bytes
    with pytest.raises(ValueError, match="size"):
        validate_pdf_bytes(b"%PDF" + b"x" * 200, max_bytes=100)


def test_compute_sha256():
    from app.storage import compute_sha256
    h = compute_sha256(b"hello")
    assert len(h) == 64
    assert compute_sha256(b"hello") == h   # deterministic


# ── Chapter parser ────────────────────────────────────────────────────────────

def test_chapter_parser_from_text():
    from app.chapter_parser import parse_chapters_from_text
    from app.pdf_processor import ExtractedPage

    pages = [
        ExtractedPage(1, "Introduction\nSome text", False, False, False),
        ExtractedPage(3, "CHAPTER 1\nMechanics\nSome content", False, False, False),
        ExtractedPage(15, "CHAPTER 2\nThermodynamics\nMore content", False, False, False),
    ]
    chapters = parse_chapters_from_text("book1", pages)
    assert len(chapters) >= 2
    titles = [c.title for c in chapters]
    assert any("Mechanics" in t for t in titles)


def test_chapter_parser_fallback_single_chapter():
    from app.chapter_parser import detect_chapters
    from app.pdf_processor import ExtractedPage, PDFMeta

    meta = PDFMeta(title="Test", author="", total_pages=5, toc=[])
    pages = [ExtractedPage(i, f"Page {i} text", False, False, False) for i in range(1, 6)]
    chapters = detect_chapters("bk", meta, pages)
    assert len(chapters) >= 1


# ── Question extractor ────────────────────────────────────────────────────────

def test_extract_inline_example():
    from app.question_extractor import extract_questions_from_chapter
    from app.models import ChapterRecord, QuestionType

    ch = ChapterRecord(
        chapter_id="bk_ch001", book_id="bk", number=1,
        title="Mechanics", page_start=1, page_end=2,
        confidence=1.0, source="toc",
    )
    pages = [
        {
            "page_number": 1,
            "text": (
                "Some introductory text.\n"
                "Example 1.1\nA car moves at 60 km/h. Find the distance in 2 hours.\n"
                "Solution: distance = speed × time = 60 × 2 = 120 km.\n"
            ),
        }
    ]
    qs = extract_questions_from_chapter("bk", ch, pages)
    assert len(qs) >= 1
    ex = qs[0]
    assert ex.question_type == QuestionType.example
    assert "car" in ex.question_text.lower() or "Example" in ex.question_text


def test_extract_numbered_exercises():
    from app.question_extractor import extract_questions_from_chapter
    from app.models import ChapterRecord, QuestionType

    ch = ChapterRecord(
        chapter_id="bk_ch002", book_id="bk", number=2,
        title="Waves", page_start=5, page_end=5,
        confidence=1.0, source="toc",
    )
    pages = [{
        "page_number": 5,
        "text": (
            "EXERCISES\n"
            "1. What is the speed of sound in air at 20°C?\n"
            "2. Define amplitude and frequency of a wave.\n"
            "3. Calculate the wavelength if speed is 340 m/s and frequency is 440 Hz.\n"
        ),
    }]
    qs = extract_questions_from_chapter("bk", ch, pages)
    types = {q.question_type for q in qs}
    assert QuestionType.exercise in types
    assert len(qs) >= 2


# ── Exporter ──────────────────────────────────────────────────────────────────

def _sample_questions():
    from app.models import QuestionRecord, QuestionType
    return [QuestionRecord(
        question_id="q1", book_id="bk", chapter_id="ch1",
        chapter_number=1, question_type=QuestionType.exercise,
        question_number="1",
        question_text="What is Newton's first law?",
        solution_text="An object at rest stays at rest.",
        answer_text=None, page_start=10, page_end=10, confidence=0.9,
    )]


def _sample_chapters():
    from app.models import ChapterRecord
    return [ChapterRecord(
        chapter_id="ch1", book_id="bk", number=1,
        title="Mechanics", page_start=1, page_end=20,
        confidence=1.0, source="toc",
    )]


def test_export_json():
    from app.exporter import to_json
    data = to_json(_sample_questions())
    import json
    records = json.loads(data)
    assert records[0]["question_text"] == "What is Newton's first law?"


def test_export_csv():
    from app.exporter import to_csv
    data = to_csv(_sample_questions())
    assert b"Newton" in data
    assert b"question_text" in data


def test_export_html():
    from app.exporter import to_html
    data = to_html(_sample_questions(), _sample_chapters(), "Test Book")
    assert b"Newton" in data
    assert b"Mechanics" in data


def test_export_no_solutions():
    from app.exporter import to_json
    data = to_json(_sample_questions(), include_solutions=False)
    import json
    records = json.loads(data)
    assert "solution_text" not in records[0]
