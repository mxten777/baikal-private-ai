"""
Chat API - AI 질문응답
"""
import json
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.chat import (
    ChatSessionCreate, ChatSessionResponse,
    ChatMessageResponse, AskRequest, AskResponse,
)
from app.models.document import ChatSession, ChatMessage
from app.models.user import User
from app.core.deps import get_current_user
from app.services.rag_service import ask_question, ask_question_stream
from app.services.llm_service import OllamaConnectionError, OllamaModelError

logger = logging.getLogger("baikal.chat")
router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """채팅 세션 목록"""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return sessions


@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
async def create_session(
    request: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """새 채팅 세션 생성"""
    session = ChatSession(
        user_id=current_user.id,
        title=request.title,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageResponse])
async def get_messages(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """세션 메시지 목록"""
    # 세션 소유자 확인
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return messages


@router.post("/ask", response_model=AskResponse)
async def ask(
    request: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 질문응답 (RAG)"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요")

    try:
        result = await ask_question(
            question=request.question,
            session_id=request.session_id,
            user_id=current_user.id,
            db=db,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except OllamaConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except OllamaModelError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"질문응답 오류: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="AI 답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")


@router.post("/ask/stream")
async def ask_stream(
    request: AskRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """AI 질문응답 스트리밍 (SSE)"""
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="질문을 입력해주세요")

    async def event_generator():
        try:
            async for event in ask_question_stream(
                question=request.question,
                session_id=request.session_id,
                user_id=current_user.id,
                db=db,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_data = {"type": "error", "content": str(e)}
            yield f"data: {json.dumps(error_data, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.delete("/sessions/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """세션 삭제"""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다")

    await db.delete(session)
    await db.commit()
