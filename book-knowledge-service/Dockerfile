FROM python:3.13-slim

# System deps: tesseract for OCR, libmupdf deps come with PyMuPDF wheel
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ── Persistent volumes ────────────────────────────────────────────────────────
# /app/storage  — database + indexed book files
# /app/books    — intake folder: drop PDFs here to auto-load on startup
# /app/secrets  — mount your .env.secrets file here (see below)
VOLUME ["/app/storage", "/app/books", "/app/secrets"]

EXPOSE 8000

# ── Runtime environment ───────────────────────────────────────────────────────
ENV STORAGE_DIR=/app/storage
ENV DATABASE_PATH=/app/storage/books.db
ENV LOG_LEVEL=INFO
ENV OCR_ENABLED=false

# ── Secrets file resolution (checked in order) ────────────────────────────────
# 1. SECRETS_FILE env var  — pass any path:
#      docker run -e SECRETS_FILE=/run/secrets/mykeys ...
# 2. /app/secrets/.env.secrets  — default volume mount location:
#      docker run -v /host/path/to/.env.secrets:/app/secrets/.env.secrets ...
# 3. /run/secrets/.env.secrets  — Docker Swarm / Compose secrets standard
# The entrypoint script sources whichever file it finds first.
ENV SECRETS_FILE=""

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
