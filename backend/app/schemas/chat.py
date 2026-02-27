"""
Chat Schemas
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ChatSessionCreate(BaseModel):
    title: str = "새 대화"


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatMessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[dict] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AskRequest(BaseModel):
    session_id: str
    question: str


class AskResponse(BaseModel):
    answer: str
    sources: List[dict]
    message_id: str
