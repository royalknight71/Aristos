from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


class StubQdrantClient:
    def __init__(self) -> None:
        self.should_fail = False
        self.closed = False

    def get_collections(self) -> None:
        if self.should_fail:
            raise RuntimeError("private connection detail")

    def close(self) -> None:
        self.closed = True


@pytest.fixture
def application(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> Iterator[tuple[object, StubQdrantClient]]:
    client = StubQdrantClient()
    monkeypatch.setattr("app.main.create_qdrant_client", lambda _settings: client)
    app = create_app(Settings(database_path=tmp_path / "aristos.sqlite"))
    yield app, client


def test_application_starts_and_initializes_database(application) -> None:
    app, qdrant_client = application
    with TestClient(app) as client:
        response = client.get("/openapi.json")

    assert response.status_code == 200
    assert qdrant_client.closed
    assert app.state.database.path.is_file()


def test_health_endpoint_returns_running_status(application) -> None:
    app, _ = application
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_qdrant_health_endpoint_checks_connectivity(application) -> None:
    app, _ = application
    with TestClient(app) as client:
        response = client.get("/health/qdrant")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_qdrant_health_endpoint_hides_connection_errors(application) -> None:
    app, qdrant_client = application
    qdrant_client.should_fail = True

    with TestClient(app) as client:
        response = client.get("/health/qdrant")

    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}
    assert "private connection detail" not in response.text
