# Book Knowledge Service

A FastAPI microservice for PDF textbook ingestion, full-text search, page viewing, chapter detection, question extraction, and AI-powered Q&A using IBM watsonx.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Get the code — choose your branch](#get-the-code)
3. [Set up the virtual environment](#set-up-the-virtual-environment)
4. [Install dependencies](#install-dependencies)
5. [Configure the service (.env)](#configure-the-service)
6. [Configure watsonx AI (optional)](#configure-watsonx-ai-optional)
7. [Start the server](#start-the-server)
8. [Upload and index a book](#upload-and-index-a-book)
9. [Browse the book](#browse-the-book)
10. [Extract questions (pattern-based)](#extract-questions-pattern-based)
11. [Generate questions with AI (watsonx)](#generate-questions-with-ai)
12. [Ask the book a question (watsonx RAG)](#ask-the-book-a-question)
13. [Export everything](#export-everything)
14. [Start afresh (reset)](#start-afresh-reset)
15. [Run tests](#run-tests)
16. [API reference](#api-reference)
17. [Project structure](#project-structure)
18. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Python 3.13** — install via [python.org](https://python.org) or Homebrew (`brew install python@3.13`)
- **git**
- **jq** — for pretty-printing JSON in terminal (`brew install jq`)
- **Tesseract** — *optional*, only needed if you want OCR on scanned pages (`brew install tesseract`)
- **IBM watsonx.ai account** — *optional*, only needed for AI endpoints (Steps 11–12)

Check Python version:

```bash
python3.13 --version   # should print Python 3.13.x
```

---

## Get the code

### Option A — main branch (stable, no AI endpoints)

```bash
git clone https://github.com/alokkataria101/quantum-computing.git
cd quantum-computing/book-knowledge-service
```

### Option B — dev1 branch (includes watsonx AI endpoints)

```bash
git clone https://github.com/alokkataria101/quantum-computing.git
cd quantum-computing/book-knowledge-service
git checkout dev1
```

### Option C — dev2 branch (AI endpoints + Docker + auto-load intake folder)

```bash
git clone https://github.com/alokkataria101/quantum-computing.git
cd quantum-computing/book-knowledge-service
git checkout dev2
```

> **Which branch?**
> - `main` — upload, index, extract questions; no AI, no Docker
> - `dev1` — adds IBM watsonx AI endpoints (Q&A, question generation)
> - `dev2` — everything in dev1, plus Docker support with flexible secrets file and a `books/` intake folder that auto-loads PDFs on startup

---

## Set up the virtual environment

Run this once, inside the `book-knowledge-service/` directory:

```bash
python3.13 -m venv .venv
```

> If `python3.13` is not found, use the full path: `/opt/homebrew/opt/python@3.13/bin/python3.13 -m venv .venv`

---

## Install dependencies

```bash
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Expected output ends with `Successfully installed ...`. This takes 1–3 minutes on first run.

---

## Configure the service

```bash
cp .env.example .env
```

The defaults work out of the box. Open `.env` only if you need to change:

```bash
# .env — edit these if needed, otherwise leave as-is
STORAGE_DIR=./storage          # where PDFs and DB are stored
DATABASE_PATH=./storage/books.db
MAX_UPLOAD_BYTES=104857600     # 100 MB upload limit
OCR_ENABLED=false              # set true only if tesseract is installed
TESSERACT_CMD=tesseract        # path to tesseract binary if not on PATH
RENDER_DPI=150                 # page render resolution
LOG_LEVEL=INFO
API_SECRET_KEY=                # leave empty for local use
```

> **OCR:** Leave `OCR_ENABLED=false` unless you have Tesseract installed (`brew install tesseract`). Without OCR the service still works — it uses PyMuPDF's built-in text layer, which is fast (< 30 s for 500 pages).

---

## Configure watsonx AI (optional)

> **Skip this section entirely if you do not have IBM watsonx credentials.** The service works fully without AI — only Steps 11 and 12 below will return HTTP 503.

The AI credentials live in a **shared secrets file at the repo root** — never in git.

### Step A — create `.env.secrets` at the repo root

```bash
cd ..                          # go up to quantum-computing/
cp .env.secrets.example .env.secrets
```

### Step B — fill in your credentials

Open `quantum-computing/.env.secrets` and fill in:

```bash
WATSONX_API_KEY=your-api-key-here
WATSONX_PROJECT_ID=your-project-id-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com

# Optional — override the default model (see note below)
# WATSONX_MODEL=meta-llama/llama-3-3-70b-instruct
```

Where to find these:
- **API key:** [IBM Cloud → Manage → Access → API keys](https://cloud.ibm.com/iam/apikeys) → Create
- **Project ID:** [watsonx.ai](https://dataplatform.cloud.ibm.com) → your project → Manage tab → Project ID
- **URL:** use `https://us-south.ml.cloud.ibm.com` for US, `https://eu-de.ml.cloud.ibm.com` for EU

> **Model note:** The default model is `meta-llama/llama-3-3-70b-instruct`. If startup shows `Model '...' is not supported`, add `WATSONX_MODEL=<supported-model>` to `.env.secrets`. The supported models are listed in the error message — choose an instruct model (e.g. `meta-llama/llama-3-3-70b-instruct`, `mistralai/mistral-small-3-1-24b-instruct-2503`).

### Step C — verify

```bash
cd book-knowledge-service
grep -v '^#' ../.env.secrets | grep '=' | while IFS='=' read -r k v; do
  [ -n "$v" ] && echo "$k: SET ✅" || echo "$k: EMPTY ❌"
done
```

All three keys should show `SET ✅`.

### Step D — go back to the service directory

```bash
cd book-knowledge-service
```

---

## Start the server

```bash
.venv/bin/uvicorn app.main:app --reload --port 8000
```

> **Important:** always use `.venv/bin/uvicorn`, not bare `uvicorn`. Using the bare command causes the reload subprocess to pick up system Python (which has no packages installed) and crash with `ModuleNotFoundError`.

The server is ready when you see:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
```

Open in browser:

| URL | What |
|-----|------|
| http://localhost:8000/docs | Swagger UI — interactive API docs |
| http://localhost:8000/redoc | ReDoc — alternative docs |

---

## Run with Docker (dev2)

Docker is available on the `dev2` branch. It handles secrets, the intake folder, and persistent storage all via volume mounts.

### Option A — default secrets location (recommended)

```bash
# 1. Copy your credentials into the secrets folder
cp ../../.env.secrets secrets/.env.secrets

# 2. Optionally drop PDFs to auto-load on startup
cp /path/to/book.pdf books/

# 3. Start
docker compose up --build
```

### Option B — pass any secrets file path

```bash
SECRETS_FILE=/absolute/path/to/mykeys.env docker compose up --build
```

Or with plain `docker run`:

```bash
docker build -t book-knowledge-service .

docker run --rm -p 8000:8000 \
  -e SECRETS_FILE=/mykeys/.env.secrets \
  -v /path/to/your/keys:/mykeys \
  -v $(pwd)/storage:/app/storage \
  -v $(pwd)/books:/app/books \
  book-knowledge-service
```

### Option C — no AI (zero config)

```bash
docker compose up --build
# Starts without any secrets file — all non-AI endpoints work normally
# AI endpoints return 503 with a clear message
```

### Secrets resolution order (inside the container)

The entrypoint checks these locations in order — first match wins:

| Priority | Location | How to use |
|----------|----------|------------|
| 1 | `$SECRETS_FILE` env var | `-e SECRETS_FILE=/any/path` |
| 2 | `/app/secrets/.env.secrets` | `-v ./secrets:/app/secrets` (default) |
| 3 | `/run/secrets/.env.secrets` | Docker Swarm / Compose secrets |
| 4 | Plain env vars | `-e WATSONX_API_KEY=... -e WATSONX_PROJECT_ID=...` |

### Persistent volumes

| Volume | Purpose |
|--------|---------|
| `./storage:/app/storage` | SQLite DB + indexed book files |
| `./books:/app/books` | Intake folder — auto-loaded on startup |
| `./secrets:/app/secrets` | Secrets / API keys file |

---

## Auto-load books on startup (dev2)

Drop PDF files into the `books/` folder before starting the server — they are automatically registered and indexed.

```
book-knowledge-service/
└── books/
    └── physics-part1.pdf    ← dropped here, auto-loaded on startup
```

**Works with both local Python and Docker.**

- Deduplication by SHA-256 — restarting the server never re-indexes the same file
- Indexing runs in the background — server is ready immediately
- Watch the logs for progress:

```
[autoload] Registered physics-part1.pdf → book_id=abc-123
[autoload] Indexed physics-part1.pdf (479 pages).
```

---

## Upload and index a book

Replace `<BOOK_ID>` and `<JOB_ID>` with the values returned by each command.

### Step 1 — Upload a PDF

```bash
curl -X POST http://localhost:8000/books \
     -F "file=@../misc/book1.pdf" | jq .
```

Response:
```json
{
  "book_id": "6051e137-...",
  "title": "book1",
  "status": "uploaded"
}
```

Note the `book_id`. Re-uploading the same file returns HTTP 409 (SHA-256 deduplication).

### Step 2 — List all books

```bash
curl http://localhost:8000/books | jq .
```

### Step 3 — Get book metadata

```bash
curl http://localhost:8000/books/<BOOK_ID> | jq .
```

### Step 4 — Start indexing

```bash
curl -X POST http://localhost:8000/books/<BOOK_ID>/index | jq .
```

Response:
```json
{ "job_id": "9869802c-...", "status": "pending" }
```

Note the `job_id`.

### Step 5 — Poll until done

```bash
curl http://localhost:8000/jobs/<JOB_ID> | jq '.status, .progress'
```

Keep running until `"status"` is `"done"`. With `OCR_ENABLED=false` this takes **< 30 seconds** for a 500-page book.

### Step 6 — List chapters

```bash
curl http://localhost:8000/books/<BOOK_ID>/chapters \
  | jq '.chapters[] | {number, title, chapter_id, page_start, page_end}'
```

Note the `chapter_id` of the chapter you want to work with — you'll need it for Steps 9–12.

---

## Browse the book

### Step 7 — Open the HTML viewer

Find `page_start` for your chapter from Step 6, then open in browser:

```
http://localhost:8000/viewer/<BOOK_ID>?page=<PAGE_START>
```

Use Previous / Next buttons to page through. The chapter sidebar lets you jump directly.

### Step 8 — Read a page as text

```bash
curl http://localhost:8000/books/<BOOK_ID>/pages/5 | jq '.text'
```

### Step 9 — Render a page as PNG

```bash
curl http://localhost:8000/books/<BOOK_ID>/pages/5/render -o page5.png
open page5.png
```

### Step 10 — Full-text search

```bash
curl "http://localhost:8000/books/<BOOK_ID>/search?q=Newton" | jq .
```

---

## Extract questions (pattern-based)

These steps use regex pattern matching — no AI required.

### Step 11 — Extract questions from one chapter

```bash
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/extract | jq .
# → returns { "job_id": "..." }

# Poll until done
curl http://localhost:8000/jobs/<JOB_ID> | jq '.status'
```

### Step 12 — Retrieve extracted questions

```bash
# All question types
curl "http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/questions" | jq .

# Filter by type: objective_1 | objective_2 | exercise | short_answer | worked_example | example
curl "http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/questions?question_type=exercise" | jq .
```

### Step 13 — Bulk extract all chapters at once

```bash
for ch_id in $(curl -s http://localhost:8000/books/<BOOK_ID>/chapters \
               | jq -r '.chapters[].chapter_id'); do
  echo "Extracting $ch_id..."
  curl -s -X POST http://localhost:8000/books/<BOOK_ID>/chapters/$ch_id/extract > /dev/null
  sleep 1
done
echo "All triggered — wait ~15 s then export."
```

### Step 14 — Generate N questions on a topic (pattern-based)

```bash
# 10 random Objective I MCQs from chapters matching "optics"
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=optics&count=10&question_type=objective_1&random=true" \
  | jq '.questions[] | {number: .question_number, text: .question_text}'

# 20 exercises from wave motion, in page order
curl "http://localhost:8000/books/<BOOK_ID>/questions/generate?topic=wave&count=20&question_type=exercise&random=false" \
  | jq '.questions[].question_text'
```

> `topic` matches against chapter **titles** (case-insensitive substring). Run Step 6 to see exact titles.

### Step 15 — Export entire book (all chapters, all types)

```bash
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=html" -o all_questions.html && open all_questions.html
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=json" -o all_questions.json
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=csv"  -o all_questions.csv
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=pdf"  -o all_questions.pdf
```

---

## Generate questions with AI

> **Requires:** watsonx credentials configured (see [Configure watsonx AI](#configure-watsonx-ai-optional)) and **dev1 branch**.
> Without credentials the endpoint returns HTTP 503 — the rest of the service is unaffected.

### Step 16 — Generate AI questions from a chapter

```bash
# 5 mixed questions (MCQ + short-answer + numerical), medium difficulty
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/generate-questions \
  -H "Content-Type: application/json" \
  -d '{
    "chapter_id": "<CH_ID>",
    "question_type": "mixed",
    "count": 5,
    "difficulty": "medium"
  }' | jq '.questions[] | {
    number: .number,
    type:   .type,
    q:      .question,
    opts:   .options,
    ans:    .answer
  }'
```

```bash
# 8 MCQ questions, hard difficulty
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/generate-questions \
  -H "Content-Type: application/json" \
  -d '{"chapter_id":"<CH_ID>","question_type":"mcq","count":8,"difficulty":"hard"}' \
  | jq '.questions[] | "\(.number). \(.question)\n  \(.options)\n  Answer: \(.answer)"'
```

```bash
# 5 numerical problems, easy difficulty
curl -X POST http://localhost:8000/books/<BOOK_ID>/chapters/<CH_ID>/generate-questions \
  -H "Content-Type: application/json" \
  -d '{"chapter_id":"<CH_ID>","question_type":"numerical","count":5,"difficulty":"easy"}' \
  | jq '.questions[].question'
```

**`question_type` options:**

| Value | Generates |
|-------|-----------|
| `mcq` | Multiple choice — 4 options (A)(B)(C)(D) with correct answer |
| `short` | Short-answer questions (2–4 lines) |
| `numerical` | Calculation problems with given data and numerical answer |
| `mixed` | ~⅓ of each type above |

**`difficulty` options:** `easy` · `medium` · `hard`

> Questions include proper scientific notation: **α β γ θ ω λ μ π**, superscripts (**v² m/s²**), subscripts (**v₀ F_net m₁ m₂**), fractions (**½mv²**), vectors (**F⃗ v⃗**).

---

## Ask the book a question

> **Requires:** watsonx credentials and **dev1 branch**.

### Step 17 — Ask anything about the book

The service uses FTS5 to find the most relevant pages, then sends them to IBM watsonx Granite to answer grounded in the actual book text.

```bash
# Ask a general question
curl -X POST http://localhost:8000/books/<BOOK_ID>/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain Newton third law with an example"}' \
  | jq '{answer: .answer, pages: .source_pages}'
```

```bash
# Ask within a specific chapter only
curl -X POST http://localhost:8000/books/<BOOK_ID>/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is simple harmonic motion?",
    "chapter_id": "<CH_ID>",
    "max_pages": 5
  }' | jq '.answer'
```

Response includes:
- `answer` — AI answer grounded in book text
- `source_pages` — page numbers used as context
- `chapter_title` — chapter name if restricted
- `ai_enabled` — `true` when watsonx is active

---

## Export everything

```bash
# HTML — open in browser, nicely formatted
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=html" -o questions.html
open questions.html

# JSON
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=json" -o questions.json

# CSV — open in Excel / Numbers
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=csv" -o questions.csv

# PDF — printable
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=pdf" -o questions.pdf
```

---

## Start afresh (reset)

Use this when the database is corrupted or you want a completely clean state.

```bash
# 1. Ctrl+C to stop the server

# 2. Wipe everything
rm -f storage/books.db
rm -rf storage/books storage/indexes storage/exports
mkdir -p storage/books storage/indexes storage/exports

# 3. Re-copy .env (resets OCR_ENABLED=false)
cp .env.example .env

# 4. Restart
.venv/bin/uvicorn app.main:app --reload --port 8000
```

Then re-upload and index from Step 1.

---

## Run tests

```bash
cd book-knowledge-service
.venv/bin/pytest tests/ -v --cov=app --cov-report=term-missing
```

---

## API reference

| Method | Endpoint | Auth needed | Purpose |
|--------|----------|-------------|---------|
| POST | `/books` | — | Upload a PDF |
| GET | `/books` | — | List all books |
| GET | `/books/{book_id}` | — | Book metadata and status |
| POST | `/books/{book_id}/index` | — | Start indexing job |
| GET | `/books/{book_id}/chapters` | — | List chapters |
| GET | `/books/{book_id}/pages/{n}` | — | Page text |
| GET | `/books/{book_id}/pages/{n}/render` | — | Page as PNG |
| GET | `/books/{book_id}/search?q=...` | — | Full-text search |
| POST | `/books/{book_id}/chapters/{ch_id}/extract` | — | Start pattern extraction |
| GET | `/books/{book_id}/chapters/{ch_id}/questions` | — | List extracted questions |
| GET | `/jobs/{job_id}` | — | Job progress |
| GET | `/books/{book_id}/export?fmt=json\|csv\|html\|pdf` | — | Export questions |
| GET | `/books/{book_id}/questions/generate?topic=...` | — | Pattern-based topic questions |
| POST | `/books/{book_id}/chapters/{ch_id}/generate-questions` | watsonx | AI question generation |
| POST | `/books/{book_id}/ask` | watsonx | AI Q&A (RAG) |
| GET | `/viewer/{book_id}?page=n` | — | HTML page viewer |

Full interactive docs: **http://localhost:8000/docs**

---

## Project structure

```
book-knowledge-service/
├── app/
│   ├── main.py               FastAPI app, viewer route, startup/shutdown
│   ├── config.py             Settings (env / .env file)
│   ├── models.py             Pydantic schemas
│   ├── database.py           SQLite + FTS5 schema
│   ├── storage.py            PDF storage, SHA-256 dedup
│   ├── pdf_processor.py      PyMuPDF extraction, OCR fallback, PNG render
│   ├── chapter_parser.py     TOC + regex chapter detection
│   ├── indexer.py            Page persistence, FTS5 rebuild
│   ├── question_extractor.py Pattern-based question extraction
│   ├── ai_client.py          IBM watsonx.ai wrapper (optional, graceful fallback)
│   ├── jobs.py               Async job tracking
│   ├── exporter.py           JSON / CSV / HTML / PDF export
│   └── routers/
│       ├── books.py          POST/GET /books
│       ├── index.py          /index, /chapters, /pages, /search
│       ├── questions.py      /questions, /extract, /generate (pattern)
│       ├── ai.py             /ask, /generate-questions (watsonx) — dev1 only
│       └── jobs_export.py    /jobs, /export
├── templates/
│   └── viewer.html           Jinja2 page viewer
├── tests/
│   ├── conftest.py
│   └── test_api.py
├── storage/                  git-ignored
│   ├── books/                uploaded PDFs
│   ├── indexes/              render cache
│   └── exports/              generated exports
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── requirements.txt
├── .env.example              committed — safe template
└── .env                      git-ignored — your local settings
```

Shared secrets (one level up, repo root):

```
quantum-computing/
├── .env.secrets.example      committed — safe template
└── .env.secrets              git-ignored — your real API keys
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'fastapi'` | Use `.venv/bin/uvicorn` not bare `uvicorn` |
| `DatabaseError: database disk image is malformed` | Run the **Start afresh** steps above |
| `tesseract is not installed` errors | Set `OCR_ENABLED=false` in `.env` (already the default) |
| `404` from `/questions/generate` | Run bulk extraction first (Step 13); check chapter titles match topic keyword |
| AI endpoints return `503` | watsonx credentials not set — see [Configure watsonx AI](#configure-watsonx-ai-optional) |
| `Model '...' is not supported` at startup | Add `WATSONX_MODEL=meta-llama/llama-3-3-70b-instruct` to `.env.secrets`; the supported list is printed in the error |
| `AI response could not be parsed as JSON` | Retry — occasionally the model wraps JSON in extra text; the raw text is returned as fallback |
| `409 Conflict` on upload | Same PDF already uploaded — use `GET /books` to find it |
| Indexing stuck on `pending` | Restart server; the asyncio task may not have started |
| FTS5 `rebuild` warning in logs | Harmless — happens on first index after a fresh DB |
| Docker: AI still disabled after mounting secrets | Check the log for `[entrypoint] Loading secrets from ...` — if missing, verify the file path and that the volume is mounted correctly |
| Docker: `[entrypoint] WARNING: SECRETS_FILE=... not found` | The path passed via `-e SECRETS_FILE=...` does not exist inside the container — check the volume mount |
| Docker: book in `books/` not auto-loaded | Check logs for `[autoload]` lines; ensure the `books/` volume is mounted (`-v $(pwd)/books:/app/books`) |
| Docker: `[autoload] ... already registered, skipping` | Normal on restart — SHA-256 deduplication prevents re-indexing the same file |
