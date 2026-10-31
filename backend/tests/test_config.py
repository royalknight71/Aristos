from pathlib import Path

from app.core.config import Settings


def test_qdrant_url_has_local_development_default(
    monkeypatch,
) -> None:
    monkeypatch.delenv("ARISTOS_QDRANT_URL", raising=False)

    settings = Settings(_env_file=None)

    assert settings.qdrant_url == "http://localhost:6333"


def test_database_path_defaults_to_backend_data_directory(monkeypatch) -> None:
    monkeypatch.delenv("ARISTOS_DATABASE_PATH", raising=False)

    settings = Settings(_env_file=None)
    expected = Path(__file__).resolve().parents[1] / "data" / "aristos.db"

    assert settings.database_path == expected


def test_database_path_can_be_overridden_with_environment(
    monkeypatch, tmp_path
) -> None:
    database_path = tmp_path / "custom.sqlite"
    monkeypatch.setenv("ARISTOS_DATABASE_PATH", str(database_path))

    settings = Settings(_env_file=None)

    assert settings.database_path == database_path


def test_relative_database_path_resolves_from_backend_directory(
    monkeypatch,
) -> None:
    monkeypatch.setenv("ARISTOS_DATABASE_PATH", "data/custom.sqlite")

    settings = Settings(_env_file=None)
    expected = Path(__file__).resolve().parents[1] / "data" / "custom.sqlite"

    assert settings.database_path == expected


def test_qdrant_url_uses_aristos_environment_prefix(monkeypatch) -> None:
    monkeypatch.setenv("ARISTOS_QDRANT_URL", "http://qdrant:6333")

    settings = Settings(_env_file=None)

    assert settings.qdrant_url == "http://qdrant:6333"
