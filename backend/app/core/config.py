from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = BACKEND_ROOT / "data" / "aristos.db"


class Settings(BaseSettings):
    """Environment-based settings for the API process."""

    app_name: str = "Aristos API"
    qdrant_url: str = "http://localhost:6333"
    database_path: Path = DEFAULT_DATABASE_PATH

    upload_dir: Path = BACKEND_ROOT / "data" / "uploads"
    max_upload_bytes: int = 20 * 1024 * 1024
    pdf_max_pages: int = 300
    pdf_extraction_timeout_seconds: int = 60
    max_normalized_text_bytes: int = 1 * 1024 * 1024

    model_config = SettingsConfigDict(
        env_prefix="ARISTOS_",
        case_sensitive=False,
    )

    @field_validator("database_path", mode="before")
    @classmethod
    def resolve_database_path(cls, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            return BACKEND_ROOT / path
        return path

    @field_validator("upload_dir", mode="before")
    @classmethod
    def resolve_upload_dir(cls, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            return BACKEND_ROOT / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
