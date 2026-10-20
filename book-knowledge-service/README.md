# Book Knowledge Service

A modular FastAPI microservice for PDF textbook ingestion, full-text indexing, page-by-page viewing, chapter detection, and question/example extraction.

---

## Run Locally

All commands below assume you are inside the repo root (`quantum-computing/`).

### 1 — Create the virtual environment (first time only)

```bash
cd book-knowledge-service
python3.13 -m venv .venv
```

> The project venv uses **Python 3.13**. If `python3.13` is not on your PATH, substitute the full path (e.g. `/opt/homebrew/opt/python@3.13/bin/python3.13`).

### 2 — Install dependencies (first time only)

```bash
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3 — Create your `.env` file (first time only)

```bash
cp .env.example .env
```

The defaults in `.env.example` work out of the box for local use. Edit only if you need to:
- point `STORAGE_DIR` / `DATABASE_PATH` at a different location
- set a custom `TESSERACT_CMD` if `tesseract` is not on your PATH
- add an `API_SECRET_KEY` for auth

### 4 — Start the server

```bash
.venv/bin/uvicorn app.main:app --reload --port 8000
```

> Always invoke uvicorn via `.venv/bin/uvicorn` (not a bare `uvicorn` command). Using the bare command risks picking up a system-level uvicorn that spawns worker processes with the wrong Python interpreter, causing `ModuleNotFoundError` on startup.

The server is ready when you see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 5 — Open in browser

| What | URL |
|------|-----|
| Interactive API docs (Swagger UI) | http://localhost:8000/docs |
| Alternative docs (ReDoc) | http://localhost:8000/redoc |
| HTML page viewer | http://localhost:8000/viewer/{book_id}?page=1 |

---

## Upload and Work with a Book

```bash
# 1. Upload a PDF
curl -X POST http://localhost:8000/books \
     -F "file=@../misc/hcv-1.pdf" | jq .
# → returns { "book_id": "abc123...", ... }

# 2. Start indexing (returns a job_id)
curl -X POST http://localhost:8000/books/abc123/index | jq .
# → returns { "job_id": "xyz..." }

# 3. Poll indexing progress
curl http://localhost:8000/jobs/xyz | jq .
# → { "status": "running"|"done"|"failed", "progress": 0.0–1.0 }

# 4. List detected chapters
curl http://localhost:8000/books/abc123/chapters | jq .

# 5. Extract questions from a chapter
curl -X POST http://localhost:8000/books/abc123/chapters/1/extract | jq .

# 6. Retrieve extracted questions
curl "http://localhost:8000/books/abc123/chapters/1/questions" | jq .

# 7. Full-text search
curl "http://localhost:8000/books/abc123/search?q=Newton" | jq .

# 8. Export questions
curl "http://localhost:8000/books/abc123/export?fmt=json" -o questions.json
curl "http://localhost:8000/books/abc123/export?fmt=csv"  -o questions.csv
curl "http://localhost:8000/books/abc123/export?fmt=html" -o questions.html
curl "http://localhost:8000/books/abc123/export?fmt=pdf"  -o questions.pdf
```

---

## Run Tests

```bash
cd book-knowledge-service
.venv/bin/pytest tests/ -v --cov=app --cov-report=term-missing
```

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
├── .env.example
└── .env                      (created from .env.example — git-ignored)
```

---

## Design Decisions

- **Separate concerns strictly:** viewing, indexing, and extraction are independent operations. A user can view a PDF before indexing completes.
- **FTS5 built into SQLite:** no external search service needed for the initial implementation.
- **SHA-256 deduplication:** re-uploading the same PDF returns HTTP 409 rather than creating a duplicate.
- **Async jobs:** long operations (OCR, indexing) run as background asyncio tasks; job progress is queryable via `/jobs/{id}`.
- **Copyrighted content:** never log extracted text; restrict export to authorised users; preserve source page references on every exported item.
