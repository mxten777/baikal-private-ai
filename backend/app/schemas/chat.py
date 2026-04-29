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
    document_ids: Optional[List[str]] = None  # None = 전체 문서
    use_hyde: bool = False  # P3-3: HyDE 고정확도 검색 모드


class AskResponse(BaseModel):
    answer: str
    sources: List[dict]
    message_id: str
    confidence_score: Optional[float] = None
    refusal_reason: Optional[str] = None  # Confidence Gate 거절 사유 (low_top1_score / low_confidence / no_chunks)


class FeedbackRequest(BaseModel):
    score: int  # 1 = 좋음, -1 = 나쁨


class SourceClickRequest(BaseModel):
    chunk_id: str
