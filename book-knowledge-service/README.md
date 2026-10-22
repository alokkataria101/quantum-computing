# Book Knowledge Service

A modular FastAPI microservice for PDF textbook ingestion, full-text indexing, page-by-page viewing, chapter detection, and question/example extraction.

---

## Start Afresh (reset everything)

Use this whenever the database is corrupted or you want a clean slate. The uploaded PDF in `storage/books/` is also wiped so you will need to re-upload.

```bash
cd /private/tmp/qp/quantum-computing/book-knowledge-service   # adjust path to your clone

# 1. Pull latest fixes
git pull

# 2. Stop the server (Ctrl+C in the uvicorn terminal)

# 3. Wipe database and all stored files
rm -f storage/books.db
rm -rf storage/books storage/indexes storage/exports

# 4. Recreate empty storage folders
mkdir -p storage/books storage/indexes storage/exports

# 5. Ensure OCR is disabled (tesseract not required)
cp .env.example .env          # OCR_ENABLED=false is the default

# 6. Start the server
.venv/bin/uvicorn app.main:app --reload --port 8000
```

The server is ready when you see `Application startup complete`.

Then re-upload and index:

```bash
# Upload
curl -X POST http://localhost:8000/books \
     -F "file=@../misc/book1.pdf" | jq '.book_id'

# Index (replace <BOOK_ID> with the value above)
curl -X POST http://localhost:8000/books/<BOOK_ID>/index | jq '.job_id'

# Poll until "status": "done"  (< 30 seconds with OCR off)
curl http://localhost:8000/jobs/<JOB_ID> | jq '.status, .progress'
```

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

## End-to-End Walkthrough

Each step builds on the previous one. Replace `<BOOK_ID>`, `<JOB_ID>`, and `<CH_ID>` with the IDs returned by the API.

---

### Step 1 — Upload a PDF

```bash
curl -X POST http://localhost:8000/books \
     -F "file=@../misc/book1.pdf" | jq .
```

Expected response:
```json
{
  "book_id": "<BOOK_ID>",
  "title": "book1",
  "status": "uploaded",
  "page_count": null
}
```

> **Re-uploading the same file** returns HTTP 409 (deduplication by SHA-256). Delete `storage/books.db` and `storage/books/` to reset.

---

### Step 2 — List all registered books (GET)

```bash
curl http://localhost:8000/books | jq .
```

---

### Step 3 — Get metadata for one book (GET)

```bash
curl http://localhost:8000/books/<BOOK_ID> | jq .
```

---

### Step 4 — Start indexing (POST)

```bash
curl -X POST http://localhost:8000/books/<BOOK_ID>/index | jq .
```

Expected response:
```json
{ "job_id": "<JOB_ID>", "status": "running" }
```

---

### Step 5 — Poll the indexing job (GET)

```bash
curl http://localhost:8000/jobs/<JOB_ID> | jq .
```

Expected response once complete:
```json
{ "job_id": "<JOB_ID>", "status": "done", "progress": 1.0 }
```

Keep polling until `"status"` is `"done"` or `"failed"`.

---

### Step 6 — List detected chapters (GET)

```bash
curl http://localhost:8000/books/<BOOK_ID>/chapters | jq .
```

Note the `"id"` field of the chapter you want — that is `<CH_ID>`.

---

### Step 7 — Read a specific page (GET)

```bash
# Extracted text for page 5
curl http://localhost:8000/books/<BOOK_ID>/pages/5 | jq .

# Render page 5 as PNG (save to file)
curl http://localhost:8000/books/<BOOK_ID>/pages/5/render -o page5.png
open page5.png
```

---

### Step 8 — Open the HTML viewer in browser

```
http://localhost:8000/viewer/<BOOK_ID>?page=1
```

Use the Previous / Next buttons or the chapter sidebar to navigate.

---

### Step 9 — Full-text search (GET)

```bash
curl "http://localhost:8000/books/<BOOK_ID>/search?q=Newton" | jq .
```

---

### Step 10 — Extract questions from a chapter (POST)

```bash
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/extract | jq .
# → returns { "job_id": "<JOB_ID>" }

# Poll until done
curl http://localhost:8000/jobs/<JOB_ID> | jq .
```

---

### Step 11 — Retrieve extracted questions (GET)

```bash
curl "http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/questions" | jq .
```

---

### Step 12 — Export questions (GET)

```bash
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=json" -o questions.json
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=csv"  -o questions.csv
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=html" -o questions.html
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=pdf"  -o questions.pdf
```

---

### Step 13 — Generate N questions on a topic (GET)

```bash
# 10 random Objective I questions from optics chapters
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=optics&count=10&question_type=objective_1&random=true" | jq .

# 5 exercises from Newton's Laws, in page order
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=newton&count=5&question_type=exercise&random=false" | jq .

# 8 short-answer questions from thermodynamics, randomly shuffled
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=thermodynamics&count=8&question_type=short_answer&random=true" | jq .
```

Available `question_type` values: `objective_1` · `objective_2` · `exercise` · `short_answer` · `worked_example` · `example`

> **Prerequisite:** questions must have been extracted first (Steps 10–11). The `topic` matches against chapter titles — use `GET /books/<BOOK_ID>/chapters` to see exact titles.

---

### Step 14 — Read a full chapter in the browser

Open the viewer at the chapter's first page. Use Previous / Next to page through it:

```
http://localhost:8000/viewer/<BOOK_ID>?page=<PAGE_START>
```

To find `<PAGE_START>` for a chapter:

```bash
curl http://localhost:8000/books/<BOOK_ID>/chapters | jq '.chapters[] | {number, title, page_start, page_end}'
```

To render any page as a PNG image:

```bash
curl http://localhost:8000/books/<BOOK_ID>/pages/<PAGE_NUMBER>/render -o page.png
open page.png
```

---

### Step 15 — Extract questions from ALL chapters at once (bulk extract)

Run this loop to trigger extraction for every chapter in one go, then wait ~10 seconds for all jobs to finish:

```bash
for ch_id in $(curl -s http://localhost:8000/books/<BOOK_ID>/chapters | jq -r '.chapters[].chapter_id'); do
  echo "Extracting $ch_id...";
  curl -s -X POST http://localhost:8000/books/<BOOK_ID>/chapters/$ch_id/extract > /dev/null;
  sleep 1;
done
echo "Done — wait ~10 s then proceed to export."
```

---

### Step 16 — Export the entire book's questions (all chapters, all types)

After bulk extraction is complete:

```bash
# HTML — open in browser, nicely formatted
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=html" -o all_questions.html
open all_questions.html

# JSON — machine-readable
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=json" -o all_questions.json

# CSV — open in Excel / Numbers
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=csv" -o all_questions.csv

# PDF — printable
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=pdf" -o all_questions.pdf
```

---

### Step 17 — Get all exercises (or any type) from a specific topic

Use `generate` with a high `count` and `random=false` to get everything in page order:

```bash
# All exercises from chapters matching "light" (e.g. optics)
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=light&count=100&question_type=exercise&random=false" \
  | jq '.questions[].question_text'

# All Objective I MCQs from chapters matching "motion"
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=motion&count=100&question_type=objective_1&random=false" \
  | jq '.questions[] | {number: .question_number, text: .question_text}'

# All short-answer questions from chapters matching "wave"
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=wave&count=100&question_type=short_answer&random=false" \
  | jq '.questions[].question_text'
```

> The `topic` keyword is matched against chapter **titles**. Run Step 6 (`GET /chapters`) first to see the exact titles available.

---

### Step 18 — Ask a question about the book (AI / watsonx RAG)

Requires `WATSONX_API_KEY` and `WATSONX_PROJECT_ID` set in `../../.env.secrets`.

```bash
# Ask anything — watsonx finds the relevant pages and answers from the book text
curl -X POST http://localhost:8000/books/<BOOK_ID>/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain Newton'\''s third law and give an example", "max_pages": 5}' \
  | jq '{answer: .answer, pages: .source_pages}'

# Restrict to a specific chapter
curl -X POST http://localhost:8000/books/<BOOK_ID>/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is simple harmonic motion?", "chapter_id": "<CH_ID>", "max_pages": 5}' \
  | jq '.answer'
```

---

### Step 19 — Generate AI questions with proper notation (watsonx)

```bash
# 5 mixed questions (MCQ + short + numerical) from a chapter, medium difficulty
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/generate-questions \
  -H "Content-Type: application/json" \
  -d '{"chapter_id": "<CH_ID>", "question_type": "mixed", "count": 5, "difficulty": "medium"}' \
  | jq '.questions[] | {number: .number, type: .type, question: .question, options: .options, answer: .answer}'

# 8 MCQ questions, hard difficulty
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/generate-questions \
  -H "Content-Type: application/json" \
  -d '{"chapter_id": "<CH_ID>", "question_type": "mcq", "count": 8, "difficulty": "hard"}' \
  | jq '.questions[] | "\(.number). \(.question)\n  Options: \(.options)\n  Answer: \(.answer)"'

# 5 numerical problems, medium difficulty
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/generate-questions \
  -H "Content-Type: application/json" \
  -d '{"chapter_id": "<CH_ID>", "question_type": "numerical", "count": 5, "difficulty": "medium"}' \
  | jq '.questions[].question'
```

Available `question_type`: `mcq` · `short` · `numerical` · `mixed`
Available `difficulty`: `easy` · `medium` · `hard`

> Questions are generated with proper scientific notation: Greek letters (α β γ θ ω λ), superscripts (v², m/s²), subscripts (v₀, F_net), fractions, and vector notation (F⃗).

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
| GET | `/books/{book_id}/questions/generate?topic=...&count=N&question_type=...&random=true\|false` | Generate N questions on a topic |
| POST | `/books/{book_id}/ask` | Ask a question — watsonx RAG answer grounded in book text |
| POST | `/books/{book_id}/chapters/{ch_id}/generate-questions` | Generate AI questions with proper notation (MCQ / short / numerical) |
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
