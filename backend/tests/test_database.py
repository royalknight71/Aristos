import sqlite3

from app.storage.database import SQLiteDatabase


def test_database_initialization_creates_parent_directory_and_file(tmp_path) -> None:
    database_path = tmp_path / "nested" / "aristos.sqlite"

    SQLiteDatabase(database_path).initialize()

    assert database_path.is_file()


def test_documents_table_has_exact_approved_schema(tmp_path) -> None:
    database_path = tmp_path / "aristos.sqlite"
    SQLiteDatabase(database_path).initialize()

    with sqlite3.connect(database_path) as connection:
        columns = connection.execute("PRAGMA table_info(documents)").fetchall()

    assert [(column[1], column[2]) for column in columns] == [
        ("id", "TEXT"),
        ("original_filename", "TEXT"),
        ("storage_key", "TEXT"),
        ("status", "TEXT"),
    ]
    assert columns[0][5] == 1
    assert all(column[3] == 1 for column in columns[1:])


def test_document_metadata_can_be_inserted_and_retrieved(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "aristos.sqlite")
    database.initialize()

    database.insert_document(
        document_id="doc-1",
        original_filename="spec.md",
        storage_key="documents/doc-1/spec.md",
        status="ready",
    )

    assert database.get_document("doc-1") == {
        "id": "doc-1",
        "original_filename": "spec.md",
        "storage_key": "documents/doc-1/spec.md",
        "status": "ready",
    }
    assert database.get_document("missing") is None


def test_repeated_initialization_preserves_existing_metadata(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "aristos.sqlite")
    database.initialize()
    database.insert_document(
        document_id="doc-1",
        original_filename="spec.md",
        storage_key="documents/doc-1/spec.md",
        status="ready",
    )

    database.initialize()

    assert database.get_document("doc-1") == {
        "id": "doc-1",
        "original_filename": "spec.md",
        "storage_key": "documents/doc-1/spec.md",
        "status": "ready",
    }


def test_storage_key_rejects_absolute_paths(tmp_path) -> None:
    database = SQLiteDatabase(tmp_path / "aristos.sqlite")
    database.initialize()

    try:
        database.insert_document(
            document_id="doc-1",
            original_filename="spec.md",
            storage_key=str(tmp_path / "spec.md"),
            status="ready",
        )
    except ValueError as error:
        assert str(error) == "storage_key must be a relative path"
    else:
        raise AssertionError("absolute storage keys must be rejected")
