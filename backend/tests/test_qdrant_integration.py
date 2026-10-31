import sys
from types import ModuleType

from app.core.config import Settings
from app.integrations.qdrant import create_qdrant_client


def test_qdrant_client_uses_configured_url(monkeypatch) -> None:
    captured: dict[str, str] = {}

    class StubQdrantClient:
        def __init__(self, *, url: str) -> None:
            captured["url"] = url

    qdrant_module = ModuleType("qdrant_client")
    qdrant_module.QdrantClient = StubQdrantClient
    monkeypatch.setitem(sys.modules, "qdrant_client", qdrant_module)

    create_qdrant_client(Settings(qdrant_url="http://qdrant.internal:6333"))

    assert captured["url"] == "http://qdrant.internal:6333"
