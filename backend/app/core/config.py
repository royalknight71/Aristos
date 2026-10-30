from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-based settings for the API process."""

    app_name: str = "Aristos API"

    model_config = SettingsConfigDict(env_prefix="ARISTOS_", case_sensitive=False)


@lru_cache
def get_settings() -> Settings:
    return Settings()
