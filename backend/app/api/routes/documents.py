import uuid
from fastapi import APIRouter, UploadFile, HTTPException, status
from app.ingestion.service import ingest_document
from pydantic import BaseModel

router = APIRouter(prefix="/documents", tags=["documents"])

class DocumentResponse(BaseModel):
    id: str
    original_filename: str
    status: str

@router.post("/", response_model=DocumentResponse)
def upload_document(file: UploadFile):
    """Endpoint to upload a document and run the ingestion pipeline."""
    result = ingest_document(file)
    return result
    """Endpoint to upload a document and run the ingestion pipeline."""
    result = ingest_document(file)
    return result
