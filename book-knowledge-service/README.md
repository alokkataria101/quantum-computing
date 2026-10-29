# Book Knowledge Service

A FastAPI microservice for PDF textbook ingestion, full-text search, page viewing, chapter detection, question extraction, and AI-powered Q&A using IBM watsonx.

---

## Authentication

Every page and API endpoint requires a login, except `/login`, `/auth/login`, `/health`, `/` and the API docs (`/docs`, `/redoc`). There are two user types:

| | Admin | Student |
|---|:---:|:---:|
| List books, read pages, view chapters, search | ✅ | ✅ |
| View extracted questions, export | ✅ | ✅ |
| **⚙ Extract** questions from a chapter | ✅ | ✅ |
| **💬 Ask AI** about the whole book or one chapter | ✅ | ✅ |
| **📢 Shared** tab — questions the admin has published | ✅ | ✅ (read-only) |
| **⚡ Generate** AI questions | ✅ | — |
| Edit, share and unshare generated questions | ✅ | — |
| Upload / delete / index books | ✅ | — |
| Add students | ✅ | — |

**Generate → edit → share → students see it.** On a chapter page the admin opens **⚡ Generate**, creates questions, and on each one can click **✎ Edit** (question, options, answer, hint) and **📢 Share** — or **Share all in batch**. Shared questions are saved in the database and appear in every user's **📢 Shared** tab for that chapter. The admin can edit or **Unshare** them there at any time. They survive re-indexing and are removed only when the book is deleted.

**Credentials are plain-text files** (`username:password`, one per line, `#` comments allowed), kept in `storage/auth/` (git-ignored):

```
storage/auth/admins.txt      # created on first start with:  admin:adminpassword
storage/auth/students.txt    # appended to when an admin adds a student
```

> **Change the default admin password** by editing `storage/auth/admins.txt`. The files are re-read on every login, so edits apply without a restart. Passwords are stored unhashed by design — fine for local use, not for a public deployment (use HTTPS and a reverse proxy at minimum).

Sign in at **http://localhost:8000/login** (choose *Admin* or *Student*). Admins get a **Students** link in the header to add students (name + password → appended to `students.txt`) and a **Delete** button on each book. Sessions last 12 hours and are stored (token hashed) in `storage/auth/sessions.db`, so they survive a restart and are shared by every server worker.

### Many users at once

Any number of users can be logged in at the same time, each with their own session. Slow work (watsonx calls, PDF indexing/rendering, extraction, export) runs in worker threads, so it never freezes the site for other users. To use more CPU cores, run several worker processes — logins work across all of them:

```bash
.venv/bin/uvicorn app.main:app --port 8000 --workers 4      # no --reload with --workers
```

| Setting | Default | Meaning |
|---|---|---|
| `AI_MAX_CONCURRENCY` | `4` | Max simultaneous watsonx calls **per worker**; extra requests wait their turn instead of hitting 429 |

Notes: PyMuPDF work is serialised within one worker (it is single-threaded), so extra workers are what give parallel PDF rendering. Only run the PDF indexing job from one place at a time; the SQLite database is shared by all workers.

From the command line:

```bash
curl -c jar -X POST localhost:8000/auth/login -H 'content-type: application/json' \
     -d '{"username":"admin","password":"adminpassword","role":"admin"}'
curl -b jar -X POST localhost:8000/auth/students -H 'content-type: application/json' \
     -d '{"username":"alice","password":"wonder1"}'
curl -b jar -X DELETE localhost:8000/books/<book_id>
```

---

## Web UI

The service ships with a built-in web interface — no API knowledge needed.

| URL | What you get |
|-----|-------------|
| **http://localhost:8000/login** | Sign in as admin or student |
| **http://localhost:8000/ui/students** | Add students *(admin only)* |
| **http://localhost:8000/ui/tasks** | Student: *My Tasks* (questions assigned to me). Admin: everything shared, and with whom, with Remove / Clear this chapter / Clear all tasks buttons |
| **http://localhost:8000/ui** | Library home — all books, upload, index |
| **http://localhost:8000/ui/books/{book_id}** | Book detail — chapters list, search, re-index |
| **http://localhost:8000/ui/books/{book_id}/chapters/{chapter_id}** | Chapter page — reader, questions, AI ask |

### Library home (`/ui`)
- Upload a PDF by drag-and-drop or file picker — indexing starts automatically
- All books shown as cards with live status (uploaded / indexing / indexed / error)
- Click **Open** to enter a book, or **Index** to trigger indexing manually

### Library home (`/ui`) — admin quick links
Admins see a shortcut bar: **📋 Compiled PDFs history** · **👥 Manage Students** · **📋 Tasks**

### Book detail (`/ui/books/{id}`)
- See all chapters with page ranges — click **Open** for the full chapter UI or **Read** to jump straight to the page viewer
- Full-text search across the whole book with results linked to pages
- **💬 Ask AI** — type any question; watsonx answers from the whole book (or any one chapter you pick in the *Search in* list) and lists the chapter and page of every source
- **Re-index** button with live progress bar; **Extract All Questions** in one click
- **📄 Compile PDF** *(admin only)* — build a downloadable PDF of notes and/or questions from selected chapters without any AI; after compile succeeds, **📤 Share with Students** and **📋 View all past compiled PDFs →** links appear (see [Compile PDF](#compile-pdf-admin-only))

### Compiled PDFs history (`/ui/compiled-pdfs`) — admin only
- Lists **every PDF ever compiled** across all books — survives page refresh and restarts
- Filter by book or mode
- **⬇ Download** any past PDF · **📤 Share** any past PDF with all students or specific ones
- "shared" badge shown on already-shared entries

### Chapter page (`/ui/books/{id}/chapters/{ch_id}`)
- **Left half**: page-by-page reader — OCR images with keyboard navigation (← →), toggle extracted text
- **Right half — tabs**:
  - **Questions** — filtered by type (Exercise / Example / MCQ / Short Answer…), show/hide answers, "Go to page" link
  - **⚡ Generate** *(admin)* — pick type (MCQ / Short / Numerical / Mixed), difficulty, and count; AI generates questions with answers; edit and share them
  - **📢 Shared** — questions the admin has published for this chapter

---

## Table of Contents

0. [Authentication](#authentication)
1. [Prerequisites](#prerequisites)
2. [Get the code](#get-the-code)
3. [Set up the virtual environment](#set-up-the-virtual-environment)
4. [Install dependencies](#install-dependencies)
5. [Configure the service (.env)](#configure-the-service)
6. [Configure watsonx AI (optional)](#configure-watsonx-ai-optional)
7. [Start the server](#start-the-server)
8. [Web UI quick start](#web-ui)
9. [Upload and index a book](#upload-and-index-a-book)
10. [Browse the book](#browse-the-book)
11. [Extract questions (pattern-based)](#extract-questions-pattern-based)
12. [Generate questions with AI (watsonx)](#generate-questions-with-ai)
13. [Ask the book a question (watsonx RAG)](#ask-the-book-a-question)
14. [Export everything](#export-everything)
15. [Start afresh (reset)](#start-afresh-reset)
16. [Run tests](#run-tests)
17. [API reference](#api-reference)
18. [Project structure](#project-structure)
19. [Troubleshooting](#troubleshooting)

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

```bash
git clone https://github.com/alokkataria101/quantum-computing.git
cd quantum-computing/book-knowledge-service
```

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
| **http://localhost:8000/ui** | **Web UI — library, books, chapters, AI ask** |
| http://localhost:8000/docs | Swagger UI — interactive API docs |
| http://localhost:8000/redoc | ReDoc — alternative docs |

---

## Web UI quick start

Once the server is running, open **http://localhost:8000/ui** in your browser.

1. **Upload** — drag-and-drop a PDF onto the upload area (or click to browse) → indexing starts automatically
2. **Open** — click the book card once status shows `indexed`
3. **Ask AI** — on the book page, type a question under **💬 Ask AI**; the answer comes from the whole book (or one chapter, via *Search in*) with the chapter and page of each source
4. **Chapter** — click **Open** on any chapter row
5. **Read** — page images load on the left; use ← → keys to navigate
6. **Questions** — switch to the **Questions** tab to browse extracted exercises and examples; filter by type
7. **Generate** — switch to **⚡ Generate**, pick type/difficulty/count, click Generate

> AI features (Ask and Generate) require watsonx credentials in `.env.secrets`. Without them all other UI features work normally.

---

## Run with Docker

> **Requires:** Docker Desktop installed and running (whale icon in menu bar). No Python needed.
> Download: https://www.docker.com/products/docker-desktop/

---

### What you need before starting

- Docker Desktop running
- Your IBM watsonx API key and Project ID *(optional — skip if you don't need AI)*
- Your PDF books *(optional — you can also upload them via the API later)*

---

### Folder layout

The repo already has these folders inside `book-knowledge-service/`. You just fill them:

```
book-knowledge-service/
├── books/                  ← DROP YOUR PDFs HERE (auto-indexed on startup)
├── secrets/
│   └── .env.secrets        ← PUT YOUR API KEYS HERE (you create this file)
├── storage/                ← created automatically; do not touch
├── Dockerfile
├── docker-compose.yml
└── app/
```

Both `books/` and `secrets/` are git-ignored — your files stay only on your machine.

---

### Step 1 — Get the code

```bash
git clone https://github.com/alokkataria101/quantum-computing.git
cd quantum-computing/book-knowledge-service
```

---

### Step 2 — Add your API keys

Create `secrets/.env.secrets` with your watsonx credentials:

```bash
# Run this from inside book-knowledge-service/
cat > secrets/.env.secrets << 'EOF'
WATSONX_API_KEY=your-api-key-here
WATSONX_PROJECT_ID=your-project-id-here
WATSONX_URL=https://us-south.ml.cloud.ibm.com
EOF
```

Where to find these values:
- **API key** → [IBM Cloud → Manage → Access → API keys](https://cloud.ibm.com/iam/apikeys) → Create
- **Project ID** → [watsonx.ai](https://dataplatform.cloud.ibm.com) → your project → Manage tab → Project ID

> **No watsonx account?** Skip this step entirely. The service starts and works without it — only the `/ask` and `/generate-questions` endpoints return HTTP 503 until credentials are added.

---

### Step 3 — Add your PDF books *(optional)*

```bash
cp /path/to/your/book.pdf books/
```

Every PDF in `books/` is automatically registered and indexed when the container starts. You can also skip this and upload books through the API (`POST /books`) after the server is running.

---

### Step 4 — Build the image

Run this once from inside `book-knowledge-service/`:

```bash
docker build -t book-knowledge-service .
```

First build takes 2–3 minutes. Rebuild only needed when code changes.

---

### Step 5 — Start the service

```bash
docker compose up
```

The service is ready when you see all three of these lines:

```
[entrypoint] Loading secrets from /app/secrets/.env.secrets
[AI] IBM watsonx initialised (model=meta-llama/llama-3-3-70b-instruct).
INFO:     Application startup complete.
```

If you added PDFs in Step 3, you will also see:

```
[autoload] Registered book.pdf → book_id=<uuid>
[autoload] Indexed book.pdf (479 pages).
```

Open: **http://localhost:8000/docs**

---

### Step 6 — Stop

```bash
docker compose down
```

`storage/` persists across restarts — your indexed books and DB are never lost. Next time just run `docker compose up` — no rebuild needed.

---

### Advanced — secrets file in a custom location

If your `.env.secrets` lives somewhere else (e.g. at the repo root from a previous setup):

```bash
# Option 1 — copy it into the secrets/ folder (recommended)
cp ../../.env.secrets secrets/.env.secrets

# Option 2 — point to it via environment variable
SECRETS_FILE=/absolute/path/to/.env.secrets docker compose up
```

The entrypoint checks these locations in order — first match wins:

| Priority | Location | How to set |
|----------|----------|------------|
| 1 | `$SECRETS_FILE` env var | `SECRETS_FILE=/path docker compose up` |
| 2 | `secrets/.env.secrets` | default — just put the file there |
| 3 | `/run/secrets/.env.secrets` | Docker Swarm / Compose secrets |
| 4 | No file found | AI disabled, all other features work |

---

## Auto-load books on startup

Drop PDF files into the `books/` folder before starting — they are automatically registered and indexed. Works with both local Python and Docker.

```
book-knowledge-service/
└── books/
    └── physics-part1.pdf    ← auto-registered and indexed on next startup
```

- **Deduplication** — restarting never re-indexes the same file (checked by SHA-256)
- **Non-blocking** — indexing runs in the background; server is ready immediately
- **Log lines to watch:**

```
[autoload] Registered physics-part1.pdf → book_id=abc-123
[autoload] Indexed physics-part1.pdf (479 pages).
[autoload] physics-part1.pdf already registered (book_id=abc-123), skipping.   ← on restart
```

---

## Setup and Run on Ubuntu (personal reference)

> Docker Desktop already installed and running. Python 3.13 not required on the host.

### 1. Clone the repository

```bash
mkdir -p /tmp/quantum-project
cd /tmp/quantum-project

git clone https://github.com/alokkataria101/quantum-computing.git
cd quantum-computing/book-knowledge-service

git pull
```

---

### 2. Configure secrets

Create the secrets file at the repo root:

```bash
cd ..
vi .env.secrets
```

Fill in your IBM watsonx.ai credentials:

```bash
WATSONX_API_KEY=your_api_key
WATSONX_PROJECT_ID=your_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

Save, then return to the service directory and copy into the secrets folder:

```bash
cd book-knowledge-service
cp ../.env.secrets secrets/.env.secrets
```

> Never commit `.env.secrets` or expose your API key publicly.

---

### 3. Build the Docker image

From inside `book-knowledge-service/`:

```bash
docker build -t book-knowledge-service .
```

First build takes 2–3 minutes. The image uses Python 3.13 — no host Python needed.

---

### 4. Start the service

```bash
docker compose up          # foreground (see logs live)
# or
docker compose up -d       # background (detached)
```

Look for these lines to confirm it started correctly:

```
[entrypoint] Loading secrets from /app/secrets/.env.secrets
[AI] IBM watsonx initialised (model=meta-llama/llama-3-3-70b-instruct).
INFO:     Application startup complete.
```

---

### 5. Access the application

| Resource | URL |
|---|---|
| Home / health | http://localhost:8000 |
| API docs (Swagger) | http://localhost:8000/docs |
| Books API | http://localhost:8000/books |

---

### 6. Upload and use a book

1. Open **http://localhost:8000/docs**
2. `POST /books` — upload a PDF
3. `POST /books/{book_id}/index` — index it
4. `POST /books/{book_id}/ask` — ask a question (AI)
5. `POST /books/{book_id}/chapters/{chapter_id}/generate-questions` — generate questions (AI)
6. Explore chapter, page, search, and export endpoints

---

### 7. View logs

```bash
docker compose logs -f
```

---

### 8. Stop the service

```bash
# Foreground: Ctrl+C
# Background:
docker compose down
```

`storage/` is preserved — your indexed books and DB persist across restarts.

---

### 9. Restart

```bash
cd /tmp/quantum-project/quantum-computing/book-knowledge-service
docker compose up -d
```

---

### 10. Expose publicly with ngrok

ngrok gives you a public HTTPS URL to access the service from outside your machine.

> **Prerequisite:** service must be running on port 8000.

**Start ngrok** (new terminal):

```bash
ngrok http 8000
```

Wait for:

```
Session Status: online
Forwarding: https://<your-ngrok-url> -> http://localhost:8000
```

**Access remotely** using the HTTPS URL ngrok shows:

| Resource | URL |
|---|---|
| Application | https://\<your-ngrok-url\> |
| API docs | https://\<your-ngrok-url\>/docs |
| Books API | https://\<your-ngrok-url\>/books |

**Monitor requests:** http://127.0.0.1:4040 — ngrok web UI for inspecting live traffic.

**Stop ngrok:** `Ctrl+C` in the ngrok terminal.

> **Security:** the public URL is reachable from the internet. Don't expose sensitive documents without access controls. Keep your watsonx credentials private — they are never sent to ngrok.

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

## Compile PDF (admin only)

Compile a ready-to-download PDF directly from the original book pages — **no AI required**.
Every question, figure, and equation is cropped from the actual printed page so nothing is lost in translation.

### Modes

| Mode | What it produces |
|------|-----------------|
| `questions` | Two-column question-card PDF grouped by chapter and category (Examples, Exercises, Short-Answer, Objective I/II, Worked Examples) |
| `notes` | Full chapter notes — every page body rendered as an image strip, grouped by chapter with headings |
| `both` | A single combined PDF: Part 1 Notes + Part 2 Questions |

### Via the UI (recommended)

1. Open a book's detail page (`/ui/books/{id}`)
2. Click **📄 Compile PDF (Notes / Questions)** in the book hero
3. Select chapters (all pre-checked), mode, and quality (DPI)
4. Click **▶ Compile PDF** — a purple progress bar tracks the background job
5. When done: **⬇ Download PDF** · **📤 Share with Students** · **📋 View all past compiled PDFs →**

Every successful compile is **permanently recorded** — go to `/ui/compiled-pdfs` at any time to download or share past PDFs.

### Share a compiled PDF with students

After a compile finishes (or from the history page):
1. Click **📤 Share with Students**
2. Enter an optional label and optionally specific student usernames (blank = all students)
3. Click **✓ Share now**

Students see the shared PDF on the **Tasks** page (`/ui/tasks`) → **⬇ Download**

### Via the API

```bash
# Start a compile job — questions only, all chapters
curl -X POST http://localhost:8000/books/<BOOK_ID>/compile-pdf \
  -H "Content-Type: application/json" \
  -d '{"mode": "questions", "dpi": 170, "chapter_ids": []}' | jq .
# → { "job_id": "...", "message": "...", "compile_id": "..." }

# Specific chapters only
curl -X POST http://localhost:8000/books/<BOOK_ID>/compile-pdf \
  -H "Content-Type: application/json" \
  -d '{"mode": "notes", "dpi": 130, "chapter_ids": ["<CH_ID_1>","<CH_ID_2>"]}' | jq .

# Poll until done — message contains compile_id when successful
curl http://localhost:8000/jobs/<JOB_ID> | jq '{status: .status, message: .message}'

# Download the finished PDF (by job_id — direct after compile)
curl -OJ http://localhost:8000/books/<BOOK_ID>/compile-pdf/<JOB_ID>/download

# List all compile history for a book
curl http://localhost:8000/books/<BOOK_ID>/compiled-pdfs | jq '.pdfs[] | {label, mode, page_count, chapters_desc}'

# List ALL compile history across all books
curl http://localhost:8000/compiled-pdfs | jq '.pdfs[] | {book_title, label, mode, created_at}'

# Download any past compile by compile_id
curl -OJ http://localhost:8000/compiled-pdfs/<COMPILE_ID>/download

# Share a compiled PDF with all students
curl -X POST http://localhost:8000/compiled-pdfs/<COMPILE_ID>/share \
  -H "Content-Type: application/json" \
  -d '{"label": "Physics Book 1 — Ch 3 Notes"}' | jq .

# Share with specific students only
curl -X POST http://localhost:8000/compiled-pdfs/<COMPILE_ID>/share \
  -H "Content-Type: application/json" \
  -d '{"label": "For Alice and Bob", "students": ["alice", "bob"]}' | jq .

# List shared PDFs visible to the caller
curl http://localhost:8000/shared-pdfs | jq '.pdfs[] | {label, mode, shared_by}'

# Download a shared PDF (student or admin)
curl -OJ http://localhost:8000/shared-pdfs/<SHARE_ID>/download

# Unshare a compiled PDF
curl -X DELETE http://localhost:8000/shared-pdfs/<SHARE_ID>
```

**`dpi` options:** `130` (draft, fast) · `170` (standard) · `220` (high quality, slow)

> **Note:** Large books (400+ pages) in `both` mode can take 3–5 minutes. The job runs in the background; the UI polls every 2 seconds automatically.

---

## Generate questions with AI

> **Requires:** watsonx credentials configured (see [Configure watsonx AI](#configure-watsonx-ai-optional)).
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

> **Requires:** watsonx credentials.

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

**Access:** *User* = any logged-in admin or student · *Admin* = admin only · *Public* = no login. Unauthenticated API calls get `401`, a student calling an admin endpoint gets `403`, and unauthenticated browser pages redirect to `/login`.

| Method | Endpoint | Access | Purpose |
|--------|----------|--------|---------|
| POST | `/auth/login` | Public | Log in (`username`, `password`, `role`) — sets session cookie |
| POST | `/auth/logout` | Public | End the session |
| GET | `/auth/me` | User | Current user |
| GET | `/auth/students` | Admin | List student names |
| POST | `/auth/students` | Admin | Add a student (`username`, `password`) |
| POST | `/books` | Admin | Upload a PDF |
| DELETE | `/books/{book_id}` | Admin | Delete a book, its chapters/questions/index and files |
| GET | `/books` | User | List all books |
| GET | `/books/{book_id}` | User | Book metadata and status |
| POST | `/books/{book_id}/index` | Admin | Start indexing job |
| GET | `/books/{book_id}/chapters` | User | List chapters |
| GET | `/books/{book_id}/pages/{n}` | User | Page text |
| GET | `/books/{book_id}/pages/{n}/render` | User | Page as PNG |
| GET | `/books/{book_id}/search?q=...` | User | Full-text search |
| POST | `/books/{book_id}/chapters/{ch_id}/extract` | User | Start pattern extraction |
| GET | `/books/{book_id}/chapters/{ch_id}/questions` | User | List extracted questions |
| GET | `/jobs/{job_id}` | User | Job progress |
| GET | `/books/{book_id}/export?fmt=json\|csv\|html\|pdf` | User | Export questions |
| POST | `/books/{book_id}/compile-pdf` | Admin | Start a compile-PDF job (notes/questions/both, chapter selection) |
| GET | `/books/{book_id}/compile-pdf/{job_id}/download` | Admin | Download compiled PDF by job ID |
| POST | `/books/{book_id}/compile-pdf/{job_id}/share` | Admin | Share a just-compiled PDF with students |
| GET | `/books/{book_id}/compiled-pdfs` | Admin | List all past compiles for a book |
| GET | `/compiled-pdfs` | Admin | List all past compiles across every book |
| GET | `/compiled-pdfs/{compile_id}/download` | Admin | Download any past compiled PDF |
| POST | `/compiled-pdfs/{compile_id}/share` | Admin | Share any past compiled PDF with students |
| DELETE | `/shared-pdfs/{share_id}` | Admin | Unshare a compiled PDF |
| GET | `/shared-pdfs` | User | List compiled PDFs shared with the caller |
| GET | `/shared-pdfs/{share_id}/download` | User | Download a shared compiled PDF |
| GET | `/books/{book_id}/questions/generate?topic=...` | Admin | Pattern-based topic questions |
| POST | `/books/{book_id}/chapters/{ch_id}/generate-questions` | Admin (+ watsonx) | AI question generation |
| POST | `/books/{book_id}/ask` | User (+ watsonx) | AI Q&A (RAG); omit `chapter_id` to search the whole book; response includes `sources` (chapter + page) |
| GET | `/books/{book_id}/chapters/{ch_id}/shared` | User | List shared questions |
| POST | `/books/{book_id}/chapters/{ch_id}/shared` | Admin | Share one or more questions |
| PUT | `/shared/{share_id}` | Admin | Edit a shared question |
| DELETE | `/shared/{share_id}` | Admin | Unshare |
| GET | `/tasks` | User | Student: questions assigned to me. Admin: everything shared |
| DELETE | `/tasks` | Admin | Clear tasks (all, or only `book_id` / `chapter_id`); returns `{"deleted": n}` |
| GET | `/viewer/{book_id}?page=n` | User | HTML page viewer |
| GET | `/login` | Public | Login page |

Full interactive docs: **http://localhost:8000/docs**

---

## Project structure

```
book-knowledge-service/
├── app/
│   ├── main.py               FastAPI app, viewer route, startup/shutdown
│   ├── config.py             Settings (env / .env file)
│   ├── auth.py               Text-file credentials, sessions, role guards
│   ├── models.py             Pydantic schemas
│   ├── database.py           SQLite + FTS5 schema
│   ├── storage.py            PDF storage, SHA-256 dedup
│   ├── pdf_processor.py      PyMuPDF extraction, OCR fallback, PNG render
│   ├── chapter_parser.py     chapters from PDF bookmarks, else the printed Table of Contents, else regex
│   ├── indexer.py            Page persistence, FTS5 rebuild
│   ├── question_extractor.py Pattern-based question extraction
│   ├── question_pdf.py       Crop questions from PDF pages into image cards
│   ├── compiler.py           Compile notes+questions PDFs without AI
│   ├── ai_client.py          IBM watsonx.ai wrapper (optional, graceful fallback)
│   ├── jobs.py               Async job tracking
│   ├── exporter.py           JSON / CSV / HTML / PDF export
│   └── routers/
│       ├── auth.py           /auth/login, /logout, /me, /students
│       ├── books.py          POST/GET/DELETE /books
│       ├── index.py          /index, /chapters, /pages, /search
│       ├── questions.py      /questions, /extract, /generate (pattern)
│       ├── ai.py             /ask, /generate-questions (watsonx)
│       ├── shared.py         admin-shared questions: list / share / edit / unshare
│       ├── compile.py        /compile-pdf, /compiled-pdfs, /shared-pdfs — compile history + sharing
│       └── jobs_export.py    /jobs, /export
├── static/
│   └── logo.svg              school crest — served at /static/logo.svg
├── templates/
│   ├── login.html            sign-in page (school branding)
│   ├── index.html            library home — admin portal / student portal
│   ├── students.html         add/list students (admin)
│   ├── compiled_pdfs.html    compiled PDFs history page (admin)
│   ├── _userbar.html         user name + logout (included in headers)
│   └── viewer.html           Jinja2 page viewer
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_auth.py          login, roles, student mgmt, book delete
│   ├── test_shared.py        share / edit / unshare, student view, page tabs per role
│   └── test_question_pdf.py  question PDF crop pipeline unit tests
├── storage/                  git-ignored
│   ├── auth/                 admins.txt, students.txt (plain-text credentials)
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

## Customising for your school

### 1 — School name

The school name **"Sri Ganesh School"** appears in four places. Replace it everywhere with a single search-and-replace:

```bash
# From inside book-knowledge-service/
grep -rn "Sri Ganesh School" templates/ static/
```

Files to update:

| File | What to change |
|---|---|
| [`templates/login.html`](templates/login.html) | `<h1>Sri Ganesh School</h1>` and footer text |
| [`templates/index.html`](templates/index.html) | `<h1>Sri Ganesh School</h1>`, tagline, footer, hero text, fallback book author |
| [`templates/compiled_pdfs.html`](templates/compiled_pdfs.html) | `<strong>Sri Ganesh School</strong>` in header |
| [`app/compiler.py`](app/compiler.py) | `"Sri Ganesh School"` string on the notes PDF cover |
| [`app/question_pdf.py`](app/question_pdf.py) | `"Sri Ganesh School"` string on the questions PDF cover |

Quick one-liner (macOS/Linux):

```bash
find templates/ app/ -type f \( -name "*.html" -o -name "*.py" \) \
  -exec sed -i '' 's/Sri Ganesh School/Your School Name/g' {} +
```

---

### 2 — School logo

The logo is an SVG file at **`static/logo.svg`**. To replace it:

1. Drop your own logo file into `book-knowledge-service/static/` — any filename works.
2. Update the `src` attribute in the three HTML templates:

```bash
# Find all logo references
grep -rn "logo.svg" templates/
```

Replace `/static/logo.svg` with `/static/your-logo.png` (or `.svg`) in each.

3. For **PDF cover pages**, the logo is loaded from the same path in Python:

```python
# app/question_pdf.py  — line near _LOGO_PATH
_LOGO_PATH = Path(__file__).resolve().parent.parent / "static" / "logo.svg"
```

Change `"logo.svg"` to match your filename.

**Supported formats:** SVG (recommended — scales perfectly), PNG, JPG — PyMuPDF handles all three.

**Logo size on pages:**
- Web header: 38–42 px display size (CSS)
- Login banner: 64 px display size (CSS)
- Questions PDF cover: 52 pt (top-right corner)
- Notes PDF cover: 88 pt (centred above title)

---

### 3 — Tagline / motto

The tagline *"Knowledge · Discipline · Excellence"* is in `templates/login.html` and `templates/index.html`:

```html
<div class="tagline">Knowledge · Discipline · Excellence</div>
<span>Digital Learning Platform</span>
```

Change both strings to your school's motto.

---

### 4 — Colour scheme

The primary navy colour `#1a3a5c` and accent gold `#c9a84c` are used throughout. To retheme:

| CSS variable usage | Files |
|---|---|
| `#1a3a5c` — primary navy | `login.html`, `index.html`, `compiled_pdfs.html`, `logo.svg` |
| `#1a6fc4` — hover/accent blue | `login.html`, `index.html` |
| `#c9a84c` — gold (logo only) | `static/logo.svg` |

Do a global replace in `templates/` and `static/` for the hex values you want to change.

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
