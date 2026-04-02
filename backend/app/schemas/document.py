import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    """Single document info — returned after upload and in document list"""
    id: uuid.UUID
    filename: str
    status: DocumentStatus
    error_message: str | None = None
    page_count: int | None = None
    chunk_count: int | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
