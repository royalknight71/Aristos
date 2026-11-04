import os
import pytest
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import get_settings
from app.storage.database import SQLiteDatabase
from app.storage.file_store import resolve_storage_path

@pytest.fixture
def client(overridden_settings):
    return TestClient(app)

def test_ready_status_failure_cleanup(monkeypatch, client, tmp_path, overridden_settings):
    # Prepare a simple txt file
    file_path = tmp_path / "doc.txt"
    file_path.write_bytes(b"content")

    captured = {}

    # Monkey‑patch update_document_status to raise on "ready"
    original_update = SQLiteDatabase.update_document_status

    def failing_update(self, doc_id, status):
        if status == "ready":
            captured["id"] = doc_id
            raise RuntimeError("Simulated ready‑status failure")
        return original_update(self, doc_id, status)

    monkeypatch.setattr(SQLiteDatabase, "update_document_status", failing_update)

    # Upload the file
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("doc.txt", f, "text/plain")})

    assert response.status_code == 500

    # Verify DB record exists with status "processing"
    settings = get_settings()
    conn = sqlite3.connect(settings.database_path)
    cur = conn.execute("SELECT status FROM documents WHERE id = ?", (captured["id"],))
    row = cur.fetchone()
    assert row is not None
    assert row[0] == "processing"

    # Verify uploaded file still exists
    stored_path = resolve_storage_path(f"{captured['id']}.txt")
    assert stored_path.is_file()

def test_symlink_escape_detection(monkeypatch, tmp_path, overridden_settings):
    settings = get_settings()
    upload_dir = settings.upload_dir

    # Create a real outside directory
    outside_dir = tmp_path / "outside"
    outside_dir.mkdir()

    # Attempt to create a symlink inside the upload dir pointing outside
    link_path = upload_dir / "link"
    try:
        # On Windows a directory symlink requires admin rights; skip if not permitted
        os.symlink(outside_dir, link_path, target_is_directory=True)
    except (OSError, NotImplementedError, PermissionError) as exc:
        pytest.skip(f"Symlink creation not permitted on this platform: {exc}")

    # Resolve a storage key that traverses through the symlink
    with pytest.raises(ValueError):
        resolve_storage_path("link/any.txt")
