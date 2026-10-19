FROM python:3.11-slim

# System deps: tesseract for OCR, libmupdf deps come with PyMuPDF wheel
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Persistent storage volumes
VOLUME ["/app/storage"]

EXPOSE 8000

ENV STORAGE_DIR=/app/storage
ENV DATABASE_PATH=/app/storage/books.db
ENV LOG_LEVEL=INFO

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
