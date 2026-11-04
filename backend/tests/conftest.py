import pytest
from pathlib import Path
from app.core.config import Settings, get_settings

@pytest.fixture
def overridden_settings(tmp_path, monkeypatch):
    """Override database and upload directories to temporary locations.

    Mirrors the fixture originally defined in test_documents.py.
    """
    db_path = tmp_path / "test.db"
    upload_dir = tmp_path / "uploads"
    monkeypatch.setenv("ARISTOS_DATABASE_PATH", str(db_path))
    monkeypatch.setenv("ARISTOS_UPLOAD_DIR", str(upload_dir))
    # Recreate Settings singleton cache
    get_settings.cache_clear()
    settings = get_settings()
    try:
        yield settings
    finally:
        # Ensure cache is cleared after test to avoid leakage
        get_settings.cache_clear()
