import uuid
import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from app.core.config import Settings, get_settings
from app.storage.file_store import store_file, delete_file
from app.storage.database import SQLiteDatabase
from app.ingestion.extractor import extract_text

logger = logging.getLogger(__name__)


def _validate_extension(filename: str) -> str:
    """Return the lower‑cased extension after ensuring it is allowed.

    Allowed extensions are .pdf, .txt, .md. Raises ``HTTPException`` with 400 if not.
    """
    ext = Path(filename).suffix.lower()
    if ext not in {".pdf", ".txt", ".md"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF, TXT, and MD are allowed.",
        )
    return ext


def ingest_document(upload_file: UploadFile) -> dict:
    """Full ingestion pipeline.

    Returns a dict with ``id``, ``original_filename`` and ``status``.
    All exceptions are translated to safe HTTP responses; unexpected errors are
    returned as 500.
    """
    settings: Settings = get_settings()

    # 1. Validate extension early (before any storage).
    _ = _validate_extension(upload_file.filename)

    # 2. Generate a UUID for the document.
    document_id = str(uuid.uuid4())
    original_filename = upload_file.filename
    try:
        # 3. Store the file.
        storage_key = store_file(upload_file, document_id=document_id)
    except ValueError as exc:
        # Size limit exceeded or other validation error.
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error during file storage")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="File storage failed")

    # 4. Insert metadata with processing status.
    db_path = settings.database_path
    database = SQLiteDatabase(db_path)
    try:
        database.initialize()
        database.insert_document(
            document_id=document_id,
            original_filename=original_filename,
            storage_key=storage_key,
            status="processing",
        )
    except Exception as exc:  # pragma: no cover
        # Cleanup the stored file because we have no DB row.
        try:
            delete_file(storage_key)
        finally:
            logger.exception("Database insert failed after storing file")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error")

    # 5. Extract and validate text.
    try:
        # Resolve absolute path for extraction.
        file_path = Path(settings.upload_dir) / storage_key
        _mime, _text = extract_text(file_path)
    except ValueError as exc:
        # Extraction/validation failure – mark failed and attempt cleanup.
        try:
            database.update_document_status(document_id, "failed")
        finally:
            try:
                delete_file(storage_key)
            except Exception as cleanup_exc:  # pragma: no cover
                logger.exception("Cleanup of source file failed after extraction error")
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc))
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected extraction error")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Extraction failed")

    # 6. Update status to ready.
    try:
        database.update_document_status(document_id, "ready")
    except Exception as exc:  # pragma: no cover
        logger.exception("Failed to update status to ready")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Status update failed")

    return {
        "id": document_id,
        "original_filename": original_filename,
        "status": "ready",
    }
