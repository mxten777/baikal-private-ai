"""
Document Schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    uploaded_by: str
    error_message: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    error_message: Optional[str] = None


class SearchResult(BaseModel):
    document_id: str
    filename: str
    content_snippet: str
    score: Optional[float] = None
