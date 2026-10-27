"""app/config.py – settings loaded from environment / .env file."""

from __future__ import annotations
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    storage_dir: Path = Path("./storage")
    database_path: Path = Path("./storage/books.db")
    max_upload_bytes: int = 100 * 1024 * 1024   # 100 MB
    tesseract_cmd: str = "tesseract"
    ocr_enabled: bool = True
    ocr_language: str = "eng"
    render_dpi: int = 150
    log_level: str = "INFO"
    api_secret_key: str = ""

    @property
    def books_dir(self) -> Path:
        return self.storage_dir / "books"

    @property
    def indexes_dir(self) -> Path:
        return self.storage_dir / "indexes"

    @property
    def exports_dir(self) -> Path:
        return self.storage_dir / "exports"

    @property
    def auth_dir(self) -> Path:
        """Plain-text credential files: admins.txt and students.txt."""
        return self.storage_dir / "auth"


settings = Settings()
