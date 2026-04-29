"""
Document Schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: int
    status: str
    uploaded_by: str
    error_message: Optional[str] = None
    is_public: bool = True
    allowed_roles: Optional[List[str]] = None
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None
    chunk_count: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentStatusResponse(BaseModel):
    id: str
    status: str
    error_message: Optional[str] = None
    total_chunks: Optional[int] = None
    processed_chunks: Optional[int] = None


class ChunkPreview(BaseModel):
    chunk_id: str
    chunk_index: int
    content: str
    document_name: str


class SearchResult(BaseModel):
    document_id: str
    filename: str
    content_snippet: str
    content: Optional[str] = None
    score: Optional[float] = None
    chunk_id: Optional[str] = None
    chunk_index: Optional[int] = None
