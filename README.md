# Quantum Computing and Physics

Hands-on quantum computing and quantum physics experiments in Python: Schrödinger-equation solvers, Hartree–Fock chemistry, the Variational Quantum Eigensolver (VQE), phase estimation, Grover/Shor demos, quantum Fourier analysis of financial and mathematical functions, and a PDF textbook knowledge service.

---

## Repository Map

| Folder | What it contains | Guide |
|---|---|---|
| [`Hamiltonian/`](Hamiltonian/) | Particle-in-a-box and hydrogen (finite differences), Hartree–Fock, H₂ with VQE, circuit basics, Grover, Shor, Monte Carlo π | [`Hamiltonian/README.md`](Hamiltonian/README.md) |
| [`phase-estimation-basics/`](phase-estimation-basics/) | From one-qubit phase measurement to full Quantum Phase Estimation | [`phase-estimation-basics/README.md`](phase-estimation-basics/README.md) |
| [`VQE/`](VQE/) | Five-step VQE tutorial: Hartree–Fock → helium → H₂ dissociation → CO₂ active space → CCSD benchmark | [`VQE/README.md`](VQE/README.md) |
| [`quantum-computing-portfolio/`](quantum-computing-portfolio/) | Six small projects (`quantum_lab` library, demos, tests, Streamlit app) | [`quantum-computing-portfolio/README.md`](quantum-computing-portfolio/README.md) |
| [`stock-analyzer/`](stock-analyzer/) | Stock analysis with quantum encodings; needs internet for most features | [`stock-analyzer/README.md`](stock-analyzer/README.md) |
| [`quantum-stock-qft/`](quantum-stock-qft/) | **Quantum Fourier Analysis of Financial Time Series** — Yahoo Finance data, Qiskit QFT, classical FFT baseline, Streamlit dashboard (7 tabs), HTML report | [`quantum-stock-qft/README.md`](quantum-stock-qft/README.md) |
| [`quantum-function-qft/`](quantum-function-qft/) | **Quantum Fourier Analysis of f(x)** — safe expression parser, 5-sample gallery, DFT vs QFT comparison, experiments tab, Streamlit dashboard | [`quantum-function-qft/README.md`](quantum-function-qft/README.md) |
| [`book-knowledge-service/`](book-knowledge-service/) | **PDF Textbook Microservice** — upload PDFs, full-text index (FTS5), page viewer, chapter detection, question extraction, bulk export, topic-based question generation | [`book-knowledge-service/README.md`](book-knowledge-service/README.md) |
| [`misc/`](misc/) | Notes and documents (untracked PDF files) | – |

---

## Quick Start by Project

### quantum-stock-qft — Quantum Fourier Analysis of Stocks

```bash
cd quantum-stock-qft
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/streamlit run app.py    # → http://localhost:8501
```

### quantum-function-qft — Quantum Fourier Analysis of f(x)

```bash
cd quantum-function-qft
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
.venv/bin/streamlit run app.py    # → http://localhost:8502
```

### book-knowledge-service — PDF Textbook Microservice

```bash
cd book-knowledge-service
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env              # OCR_ENABLED=false by default
.venv/bin/uvicorn app.main:app --reload --port 8000
# → http://localhost:8000/docs
```

> Always use `.venv/bin/uvicorn` (not bare `uvicorn`) to avoid the system Python subprocess mismatch.

---

## book-knowledge-service — End-to-End Usage

The full walkthrough is in [`book-knowledge-service/README.md`](book-knowledge-service/README.md). Here is the condensed version that has been verified to work end-to-end.

### 1. Upload a PDF

```bash
curl -X POST http://localhost:8000/books \
     -F "file=@misc/hcv-1.pdf" | jq .
# → note the "book_id"
```

### 2. Index the book

```bash
curl -X POST http://localhost:8000/books/<BOOK_ID>/index | jq .
# → note the "job_id"

# Poll until "status": "done"  (< 30 s with OCR_ENABLED=false)
curl http://localhost:8000/jobs/<JOB_ID> | jq '.status, .progress'
```

### 3. List chapters (get real titles for topic search)

```bash
curl http://localhost:8000/books/<BOOK_ID>/chapters \
  | jq '.chapters[] | {number, title, page_start, page_end}'
```

Example titles from H.C. Verma Part 1:

| Chapter | Title keyword to use |
|---------|---------------------|
| 3  | `kinematics` |
| 5  | `newton` |
| 6  | `friction` |
| 8  | `energy` |
| 11 | `gravitation` |
| 12 | `harmonic` |
| 15 | `wave` |
| 16 | `sound` |
| 17 | `light` |
| 18 | `optics` |
| 19 | `instruments` |

### 4. Read a chapter in the browser

```bash
# Find the page_start for your chapter from step 3, then open:
open "http://localhost:8000/viewer/<BOOK_ID>?page=<PAGE_START>"
```

### 5. Bulk-extract questions from all chapters

```bash
for ch_id in $(curl -s http://localhost:8000/books/<BOOK_ID>/chapters \
               | jq -r '.chapters[].chapter_id'); do
  echo "Extracting $ch_id...";
  curl -s -X POST http://localhost:8000/books/<BOOK_ID>/chapters/$ch_id/extract > /dev/null;
  sleep 1;
done
echo "Done — wait ~15 s then export."
```

### 6. Export the entire book

```bash
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=html" -o all_questions.html
open all_questions.html                   # all chapters, all question types

curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=json" -o all_questions.json
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=csv"  -o all_questions.csv
curl "http://localhost:8000/books/<BOOK_ID>/export?fmt=pdf"  -o all_questions.pdf
```

### 7. Generate N questions on a topic

```bash
BOOK_ID=<your-book-id>

# 10 random Objective I MCQs from optics
curl "http://localhost:8000/books/$BOOK_ID/questions/generate?topic=optics&count=10&question_type=objective_1&random=true" \
  | jq '.questions[] | {number: .question_number, text: .question_text}'

# 20 exercises from wave motion in page order
curl "http://localhost:8000/books/$BOOK_ID/questions/generate?topic=wave&count=20&question_type=exercise&random=false" \
  | jq '.questions[].question_text'

# 15 short-answer questions from Newton's Laws, shuffled
curl "http://localhost:8000/books/$BOOK_ID/questions/generate?topic=newton&count=15&question_type=short_answer&random=true" \
  | jq '.questions[].question_text'
```

Available `question_type` values: `objective_1` · `objective_2` · `exercise` · `short_answer` · `worked_example` · `example`

---

## Hamiltonian / VQE Projects — Prerequisites

- **Python 3.11** (tested). 3.12/3.13 will not install `numpy==1.23.5`.
- `git`, ~2 GB free disk space.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python -c "import qiskit, numpy; print('qiskit', qiskit.__version__, '| numpy', numpy.__version__)"
# Expected: qiskit 1.1.0 | numpy 1.23.5
```

### Run all Hamiltonian/VQE demos

```bash
source .venv/bin/activate
python run_all.py
# Output written to outputs/run_all_results.md
```

Options:

```bash
python run_all.py --list                   # show scripts, don't run
python run_all.py --only VQE               # only VQE scripts
python run_all.py --only phase-estimation  # only phase estimation
python run_all.py --timeout 1200           # 20 min per script (default 600 s)
python run_all.py --output my_results.md   # custom output file
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: No module named 'fastapi'` in uvicorn | Use `.venv/bin/uvicorn` not bare `uvicorn` — system Python subprocess picks up wrong interpreter |
| `DatabaseError: database disk image is malformed` | Wipe DB: `rm -f storage/books.db && rm -rf storage/books storage/indexes storage/exports` then restart |
| `tesseract is not installed` during indexing | Set `OCR_ENABLED=false` in `.env` (already the default in `.env.example`) |
| `404` from `/questions/generate` | Bulk extraction (Step 5) hasn't run yet, or `topic` doesn't match any chapter title — check titles with `GET /chapters` |
| `ImportError: cannot import name 'Estimator'` | Qiskit 2.x installed — reinstall with `pip install -r requirements.txt` in a fresh venv |
| `AttributeError: 'csr_matrix' object has no attribute 'H'` | SciPy ≥ 1.14 — root `requirements.txt` pins `scipy==1.10.1` |
| `numpy==1.23.5` has no wheel on Python 3.12/3.13 | Use Python 3.11 for Hamiltonian/VQE projects |
| Streamlit `st.dataframe()` / `st.table()` crash | pyarrow conflict — use `st.markdown(..., unsafe_allow_html=True)` with hand-built HTML table |
