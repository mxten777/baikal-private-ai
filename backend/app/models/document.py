"""
Document, Chunk, Chat Models
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import String, Integer, BigInteger, Float, Text, DateTime, ForeignKey, JSON, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base
from app.config import get_settings

settings = get_settings()

_utcnow = lambda: datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    filepath: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="uploading", nullable=False
    )  # uploading, processing, completed, failed
    uploaded_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    error_message: Mapped[str] = mapped_column(Text, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    allowed_roles: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    # P3-6 Document Lineage
    chunk_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 처리 완료 시 청크 수
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )  # 마지막 처리/수정 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    document_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    nl_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    embedding = mapped_column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)    # PDF/DOCX 페이지 번호 (1-based)
    source_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # "text" / "table" / "ocr"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    document = relationship("Document", back_populates="chunks")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), default="새 대화", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    session_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user / assistant
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )

    session = relationship("ChatSession", back_populates="messages")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    document_ids: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, nullable=False
    )
    # KPI 산출용 확장 필드 (0003 마이그레이션)
    session_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True)
    retrieved_chunks: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)   # [{chunk_id, score, rank}]
    reranked_order: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)     # [chunk_id, ...] cross-encoder 정렬 후
    cited_sources: Mapped[Optional[List]] = mapped_column(JSON, nullable=True)      # LLM 인용 chunk_id 목록
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)   # 사용 LLM 모델명
    retrieval_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)     # 검색 단계 ms
    reranking_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)     # Cross-encoder 단계 ms
    llm_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)           # LLM 생성 단계 ms
    feedback_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 1=좋음 / -1=나쁨
    click_source_flag: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)  # 출처 클릭 여부
