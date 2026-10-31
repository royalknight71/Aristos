from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.config import Settings

if TYPE_CHECKING:
    from qdrant_client import QdrantClient


def create_qdrant_client(settings: Settings) -> QdrantClient:
    """Create a Qdrant client from application settings."""
    from qdrant_client import QdrantClient as QdrantClientImplementation

    return QdrantClientImplementation(url=settings.qdrant_url)
