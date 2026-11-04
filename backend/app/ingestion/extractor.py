import io
import time
from pathlib import Path
from typing import Tuple

import fitz  # PyMuPDF

from app.core.config import Settings, get_settings


def _validate_pdf(path: Path, settings: Settings) -> None:
    """Validate a PDF file.

    Checks the PDF header and page count limits.
    """
    # Simple PDF header check
    with path.open("rb") as f:
        header = f.read(5)
        if not header.startswith(b"%PDF-"):
            raise ValueError("File does not appear to be a valid PDF")
    # Page count
    with fitz.open(str(path)) as doc:
        if doc.page_count > settings.pdf_max_pages:
            raise ValueError(f"PDF exceeds maximum page count of {settings.pdf_max_pages}")


def _extract_pdf_text(path: Path, settings: Settings) -> str:
    """Extract text from a PDF, enforcing time and size limits.

    Returns the concatenated text of all pages, each prefixed with a page marker.
    Raises ``ValueError`` on timeout or when the extracted text exceeds
    ``max_normalized_text_bytes``.
    """
    start = time.time()
    extracted_pages = []
    with fitz.open(str(path)) as doc:
        for page_num in range(doc.page_count):
            # Periodic timeout check – not a hard kill.
            if time.time() - start > settings.pdf_extraction_timeout_seconds:
                raise ValueError("PDF extraction timed out")
            page = doc.load_page(page_num)
            page_text = page.get_text()
            extracted_pages.append(f"Page {page_num + 1}:\n{page_text}")
    text = "\n\n".join(extracted_pages)
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Size limit
    if len(text.encode("utf-8")) > settings.max_normalized_text_bytes:
        raise ValueError("Extracted text exceeds maximum allowed size")
    if not text.strip():
        raise ValueError("Extracted PDF text is empty")
    return text


def _extract_text_file(path: Path, settings: Settings) -> str:
    """Read a UTF‑8 text file (TXT or MD) and apply size/emptiness checks."""
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("File is not valid UTF‑8 text") from exc
    # Normalize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if not text.strip():
        raise ValueError("Document contains no readable text")
    if len(text.encode("utf-8")) > settings.max_normalized_text_bytes:
        raise ValueError("Extracted text exceeds maximum allowed size")
    return text


def extract_text(file_path: Path) -> Tuple[str, str]:
    """Detect file type by extension and extract normalized text.

    Returns a tuple ``(mime, text)`` where ``mime`` is one of ``pdf``, ``txt`` or
    ``md``. All validation errors raise ``ValueError`` with a user‑friendly
    message.
    """
    settings = get_settings()
    ext = file_path.suffix.lower()
    if ext == ".pdf":
        _validate_pdf(file_path, settings)
        return "pdf", _extract_pdf_text(file_path, settings)
    if ext in {".txt", ".md"}:
        # mime name without leading dot
        return ext.lstrip('.'), _extract_text_file(file_path, settings)
    raise ValueError("Unsupported file extension")

