from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health", tags=["health"])
def health_check() -> dict[str, str]:
    """Report that the API process is running."""
    return {"status": "ok"}


@router.get("/health/qdrant", tags=["health"], response_model=None)
def qdrant_health_check(request: Request) -> dict[str, str] | JSONResponse:
    """Report whether the configured Qdrant service is reachable."""
    try:
        request.app.state.qdrant_client.get_collections()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "unavailable"})

    return {"status": "ok"}
