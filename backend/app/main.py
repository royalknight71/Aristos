from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import Settings, get_settings
from app.integrations.qdrant import create_qdrant_client
from app.storage.database import SQLiteDatabase


def create_app(settings: Settings | None = None) -> FastAPI:
    app_settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        qdrant_client = create_qdrant_client(app_settings)
        try:
            database = SQLiteDatabase(app_settings.database_path)
            database.initialize()
            application.state.qdrant_client = qdrant_client
            application.state.database = database
            yield
        finally:
            qdrant_client.close()

    application = FastAPI(title=app_settings.app_name, lifespan=lifespan)
    application.include_router(health_router)
    return application


app = create_app()
