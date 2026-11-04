import io
import os
import uuid
from pathlib import Path

import fitz  # PyMuPDF
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import Settings, get_settings
from app.storage.file_store import resolve_storage_path, delete_file

# Helper to create a temporary PDF with a given number of pages and optional text per page
def create_pdf(path: Path, pages: int, text_per_page: str = "Hello") -> None:
    doc = fitz.open()
    for _ in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), text_per_page)
    doc.save(str(path))
    doc.close()

@pytest.fixture
def overridden_settings(tmp_path, monkeypatch):
    # Override database and upload directories to temporary locations
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


@pytest.fixture
def client(overridden_settings):
    return TestClient(app)

def test_txt_upload_success(client, tmp_path):
    content = b"Sample text content for testing."
    file_path = tmp_path / "sample.txt"
    file_path.write_bytes(content)
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("sample.txt", f, "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "sample.txt"
    assert data["status"] == "ready"
    # Verify file exists in upload directory
    settings = get_settings()
    stored_path = resolve_storage_path(data["id"] + ".txt")
    assert stored_path.is_file()

def test_md_upload_success(client, tmp_path):
    content = b"# Markdown Title\n\nSome markdown content."
    file_path = tmp_path / "doc.md"
    file_path.write_bytes(content)
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("doc.md", f, "text/markdown")})
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "doc.md"
    assert data["status"] == "ready"

def test_pdf_upload_success(client, tmp_path):
    pdf_path = tmp_path / "sample.pdf"
    create_pdf(pdf_path, pages=2, text_per_page="Page content")
    with open(pdf_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("sample.pdf", f, "application/pdf")})
    assert response.status_code == 200
    data = response.json()
    assert data["original_filename"] == "sample.pdf"
    assert data["status"] == "ready"

def test_unsupported_extension(client, tmp_path):
    file_path = tmp_path / "image.jpg"
    file_path.write_bytes(b"fakeimage")
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("image.jpg", f, "image/jpeg")})
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]

def test_empty_txt_file(client, tmp_path):
    file_path = tmp_path / "empty.txt"
    file_path.write_bytes(b"")
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("empty.txt", f, "text/plain")})
    assert response.status_code == 422
    assert "no readable text" in response.json()["detail"].lower()

def test_invalid_pdf_header(client, tmp_path):
    # Create a file with .pdf extension but not a real PDF
    file_path = tmp_path / "bad.pdf"
    file_path.write_bytes(b"Not a PDF content")
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("bad.pdf", f, "application/pdf")})
    assert response.status_code == 422
    assert "valid pdf" in response.json()["detail"].lower()

def test_pdf_page_limit_exceeded(client, tmp_path):
    pdf_path = tmp_path / "large.pdf"
    # 301 pages to exceed limit
    create_pdf(pdf_path, pages=301)
    with open(pdf_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("large.pdf", f, "application/pdf")})
    assert response.status_code == 422
    assert "exceeds maximum page count" in response.json()["detail"].lower()

def test_normalized_text_limit_exceeded(client, tmp_path):
    # Create a txt file larger than 1 MiB
    large_content = b"a" * (1024 * 1024 + 1)
    file_path = tmp_path / "large.txt"
    file_path.write_bytes(large_content)
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("large.txt", f, "text/plain")})
    # Size limit is enforced during storage (20 MiB) but also normalized text size (1 MiB)
    assert response.status_code == 422
    assert "exceeds maximum allowed size" in response.json()["detail"].lower()

def test_oversized_upload_rejection(client, tmp_path):
    # Create a file slightly larger than 20 MiB
    large_content = b"a" * (20 * 1024 * 1024 + 1)
    file_path = tmp_path / "huge.txt"
    file_path.write_bytes(large_content)
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("huge.txt", f, "text/plain")})
    assert response.status_code == 400
    assert "exceeds maximum allowed size" in response.json()["detail"].lower()

def test_database_insert_failure_cleanup(client, tmp_path, monkeypatch):
    # Force SQLite insert to raise after file stored
    from app.storage.database import SQLiteDatabase
    original_insert = SQLiteDatabase.insert_document
    def failing_insert(self, *args, **kwargs):
        raise RuntimeError("Simulated DB failure")
    monkeypatch.setattr(SQLiteDatabase, "insert_document", failing_insert)
    # Prepare a small txt file
    file_path = tmp_path / "doc.txt"
    file_path.write_bytes(b"content")
    with open(file_path, "rb") as f:
        response = client.post("/documents/", files={"file": ("doc.txt", f, "text/plain")})
    assert response.status_code == 500
    # Ensure no file remains in upload dir
    settings = get_settings()
    assert not any(settings.upload_dir.iterdir())
    # Restore original method
    monkeypatch.setattr(SQLiteDatabase, "insert_document", original_insert)

def test_path_traversal_rejection(monkeypatch, tmp_path):
    # Directly test file_store resolution with a traversal key
    from app.storage.file_store import resolve_storage_path
    settings = get_settings()
    # Provide a malicious storage key
    with pytest.raises(ValueError):
        resolve_storage_path("../outside.txt")
