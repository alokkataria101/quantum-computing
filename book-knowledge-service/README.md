# Book Knowledge Service

A modular FastAPI microservice for PDF textbook ingestion, full-text indexing, page-by-page viewing, chapter detection, and question/example extraction.

---

## Features

| Capability | Detail |
|---|---|
| Upload & register PDFs | SHA-256 deduplication, size and header validation |
| Index | PyMuPDF text extraction + optional Tesseract OCR, FTS5 full-text search |
| Chapter detection | PDF bookmarks (TOC) → pattern-based text scanning fallback |
| Page viewer | Rendered PNG + extracted text, keyboard navigation, search, chapter sidebar |
| Question extraction | Examples, Worked Out Examples, Short Answer, Objective I/II, Exercises |
| Export | JSON · CSV · HTML · PDF (ReportLab) with source page references |
| Background jobs | Async in-process task tracking; swap in Celery+Redis for production |

---

## Quick Start

```bash
cd book-knowledge-service
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env         # edit if needed
uvicorn app.main:app --reload --port 8000
```

Open:
- **API docs:** http://localhost:8000/docs
- **Viewer:** http://localhost:8000/viewer/{book_id}?page=1

---

## Upload and Index a Book

```bash
# 1. Upload
curl -X POST http://localhost:8000/books \
     -F "file=@misc/hcv-1.pdf" | jq .

# 2. Start indexing (returns job_id)
curl -X POST http://localhost:8000/books/{book_id}/index | jq .

# 3. Poll the job
curl http://localhost:8000/jobs/{job_id} | jq .

# 4. List chapters
curl http://localhost:8000/books/{book_id}/chapters | jq .

# 5. Extract questions from a chapter
curl -X POST http://localhost:8000/books/{book_id}/chapters/{chapter_id}/extract | jq .

# 6. Get questions
curl "http://localhost:8000/books/{book_id}/chapters/{chapter_id}/questions" | jq .

# 7. Export
curl "http://localhost:8000/books/{book_id}/export?fmt=json" -o questions.json
curl "http://localhost:8000/books/{book_id}/export?fmt=html" -o questions.html
```

---

## API Reference

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/books` | Upload and register a PDF |
| GET | `/books` | List all registered books |
| GET | `/books/{book_id}` | Book metadata and status |
| POST | `/books/{book_id}/index` | Start indexing job |
| GET | `/books/{book_id}/chapters` | List detected chapters |
| GET | `/books/{book_id}/pages/{n}` | Get extracted text for page n |
| GET | `/books/{book_id}/pages/{n}/render` | Render page n as PNG |
| GET | `/books/{book_id}/search?q=...` | Full-text search in book |
| GET | `/books/{book_id}/chapters/{ch_id}/questions` | List extracted questions |
| POST | `/books/{book_id}/chapters/{ch_id}/extract` | Start extraction job |
| GET | `/jobs/{job_id}` | Check job progress |
| GET | `/books/{book_id}/export?fmt=json\|csv\|html\|pdf` | Export questions |
| GET | `/viewer/{book_id}?page=n` | HTML page viewer |

Full interactive docs at `/docs` (Swagger UI) and `/redoc`.

---

## Run Tests

```bash
pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## Docker

```bash
docker build -t book-knowledge-service .
docker run -p 8000:8000 -v $(pwd)/storage:/app/storage book-knowledge-service
```

---

## Project Structure

```
book-knowledge-service/
├── app/
│   ├── main.py               FastAPI app, viewer route, startup/shutdown
│   ├── config.py             Settings (env / .env file)
│   ├── models.py             Pydantic schemas (BookRecord, ChapterRecord, …)
│   ├── database.py           SQLite + FTS5 init and schema
│   ├── storage.py            PDF file storage, SHA-256 deduplication
│   ├── pdf_processor.py      PyMuPDF text extraction, OCR fallback, PNG render
│   ├── chapter_parser.py     TOC bookmarks + text-pattern chapter detection
│   ├── indexer.py            Page persistence, FTS5 index, book status updates
│   ├── question_extractor.py Pattern-based extraction of examples/questions
│   ├── jobs.py               Async background job tracking
│   ├── exporter.py           JSON / CSV / HTML / PDF export
│   └── routers/
│       ├── books.py          POST /books, GET /books, GET /books/{id}
│       ├── index.py          /index, /chapters, /pages, /render, /search
│       ├── questions.py      /questions, /extract
│       └── jobs_export.py    /jobs/{id}, /export
├── templates/
│   └── viewer.html           Jinja2 HTML page viewer
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── storage/                  (git-ignored except .gitkeep)
│   ├── books/                uploaded PDFs
│   ├── indexes/              render cache and future vector indexes
│   └── exports/              generated export files
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── .env.example
```

---

## Design Decisions

- **Separate concerns strictly:** viewing, indexing, and extraction are independent operations. A user can view a PDF before indexing completes.
- **FTS5 built into SQLite:** no external search service needed for the initial implementation.
- **SHA-256 deduplication:** re-uploading the same PDF returns HTTP 409 rather than creating a duplicate.
- **Async jobs:** long operations (OCR, indexing) run as background asyncio tasks; job progress is queryable via `/jobs/{id}`.
- **Copyrighted content:** never log extracted text; restrict export to authorised users; preserve source page references on every exported item.
