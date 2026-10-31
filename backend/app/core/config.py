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

    model_config = SettingsConfigDict(env_prefix="ARISTOS_", case_sensitive=False)

    @field_validator("database_path", mode="before")
    @classmethod
    def resolve_database_path(cls, value: str | Path) -> Path:
        path = Path(value)
        if not path.is_absolute():
            return BACKEND_ROOT / path
        return path


@lru_cache
def get_settings() -> Settings:
    return Settings()
