from contextlib import contextmanager
from pathlib import Path, PureWindowsPath
import sqlite3
from typing import Iterator


class SQLiteDatabase:
    """Small SQLite store for document metadata."""

    def __init__(self, database_path: Path) -> None:
        self.path = database_path

    def initialize(self) -> None:
        """Create the database directory and documents table if absent."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    original_filename TEXT NOT NULL,
                    storage_key TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                """
            )

    def insert_document(
        self,
        *,
        document_id: str,
        original_filename: str,
        storage_key: str,
        status: str,
    ) -> None:
        """Persist one document's approved metadata fields."""
        if Path(storage_key).is_absolute() or PureWindowsPath(storage_key).drive:
            raise ValueError("storage_key must be a relative path")

        with self._connection() as connection:
            connection.execute(
                """
                INSERT INTO documents (id, original_filename, storage_key, status)
                VALUES (?, ?, ?, ?)
                """,
                (document_id, original_filename, storage_key, status),
            )

    def get_document(self, document_id: str) -> dict[str, str] | None:
        """Return a document's metadata or None when it does not exist."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT id, original_filename, storage_key, status
                FROM documents
                WHERE id = ?
                """,
                (document_id,),
            ).fetchone()

        return dict(row) if row is not None else None

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
