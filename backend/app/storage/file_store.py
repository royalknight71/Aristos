import uuid
from pathlib import Path
from typing import BinaryIO

from fastapi import UploadFile
from app.core.config import Settings, get_settings


def _ensure_upload_dir(settings: Settings) -> Path:
    """Create the upload directory if missing and return it."""
    upload_dir = settings.upload_dir
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def _safe_relative_path(root: Path, target: Path) -> Path:
    """Return *target* relative to *root* after confirming it stays inside *root*.

    Raises ``ValueError`` on traversal attempts.
    """
    try:
        return target.relative_to(root)
    except Exception as exc:
        raise ValueError("Attempted path traversal outside upload directory") from exc


def store_file(upload_file: UploadFile, *, document_id: str) -> str:
    """Store an uploaded file safely.

    The file is written in 1 MiB chunks while enforcing the global size limit.
    A UUID‑derived filename (preserving the original extension) is used; the
    returned value is a POSIX‑style *relative* storage key suitable for SQLite.
    """
    settings = get_settings()
    upload_dir = _ensure_upload_dir(settings)

    # Preserve original extension only (lower‑cased).
    ext = Path(upload_file.filename).suffix.lower()
    storage_name = f"{document_id}{ext}"
    destination = upload_dir / storage_name

    bytes_written = 0
    with destination.open("wb") as out_file:
        while True:
            chunk = upload_file.file.read(1024 * 1024)  # 1 MiB per iteration
            if not chunk:
                break
            bytes_written += len(chunk)
            if bytes_written > settings.max_upload_bytes:
                # Abort and clean up partial file.
                out_file.close()
                destination.unlink(missing_ok=True)
                raise ValueError("Uploaded file exceeds maximum allowed size")
            out_file.write(chunk)

    # Return a relative path (e.g., "uploads/<filename>")
    rel_path = _safe_relative_path(settings.upload_dir, destination)
    return str(rel_path.as_posix())


def resolve_storage_path(storage_key: str) -> Path:
    """Convert a stored *storage_key* back to an absolute ``Path``.

    Validates that the key is relative and does not escape the upload directory.
    """
    settings = get_settings()
    key_path = Path(storage_key)
    if key_path.is_absolute() or key_path.drive:
        raise ValueError("storage_key must be a relative path")
    # Resolve the upload root to its canonical absolute path
    root = settings.upload_dir.resolve()
    absolute = (root / key_path).resolve()
    if not absolute.is_relative_to(root):
        raise ValueError("storage_key resolves outside allowed directory")
    return absolute
    if not absolute.is_relative_to(settings.upload_dir):
        raise ValueError("storage_key resolves outside allowed directory")
    return absolute


def delete_file(storage_key: str) -> None:
    """Delete a stored file, ignoring missing files.

    Errors are propagated to the caller for logging or further handling.
    """
    path = resolve_storage_path(storage_key)
    path.unlink(missing_ok=True)
