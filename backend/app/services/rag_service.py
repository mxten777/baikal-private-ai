"""
RAG Service - 질문응답 파이프라인
"""
import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.models.document import Document, DocumentChunk, ChatSession, ChatMessage
from app.services.llm_service import call_ollama_chat, call_ollama_chat_stream, call_ollama_embedding
from app.rag.retriever import retrieve_relevant_chunks
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("baikal.rag")

SYSTEM_PROMPT = """당신은 BAIKAL Private AI 시스템의 기업 내부 문서 전문 어시스턴트입니다.

## 핵심 규칙
1. **반드시 아래 제공된 참고 문서만을 근거로** 답변하세요.
2. 문서에 없는 내용은 추측하지 말고 "제공된 문서에서 관련 정보를 찾을 수 없습니다"라고 답변하세요.
3. 답변은 **항상 자연스러운 한국어**로 작성하세요.
4. 핵심 내용을 먼저 요약하고, 필요하면 상세 내용을 이어서 설명하세요.
5. 가능하면 구조화된 형식(번호, 불릿, 표)을 활용하세요.
6. 참고한 문서명을 답변 말미에 언급하세요."""

MAX_HISTORY_TURNS = 5  # 컨텍스트에 포함할 최대 대화 턴 수


async def _get_chat_history(session_id: str, db: AsyncSession) -> list[dict]:
    """세션의 최근 대화 히스토리를 가져옴"""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(MAX_HISTORY_TURNS * 2)  # user+assistant 쌍
    )
    messages = result.scalars().all()
    # 시간순 정렬 (오래된 것부터)
    messages = list(reversed(messages))
    return [{"role": m.role, "content": m.content} for m in messages]


async def ask_question(
    question: str, session_id: str, user_id: str, db: AsyncSession
) -> dict:
    """RAG 기반 질문응답"""

    # 1. 세션 확인
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError("채팅 세션을 찾을 수 없습니다")

    # 2. Vector 유사도 검색 (retriever 사용)
    chunks = await retrieve_relevant_chunks(question, db)

    # 3. 컨텍스트 생성
    context_parts = []
    sources = []
    seen_docs = set()

    for chunk in chunks:
        context_parts.append(f"[{chunk['filename']} - 청크 {chunk['chunk_index'] + 1}]\n{chunk['content']}")

        if chunk['document_id'] not in seen_docs:
            sources.append({
                "document_id": chunk['document_id'],
                "filename": chunk['filename'],
                "relevance_score": chunk['score'],
            })
            seen_docs.add(chunk['document_id'])

    context = "\n\n---\n\n".join(context_parts) if context_parts else "관련 문서를 찾을 수 없습니다."

    # 4. 대화 히스토리 가져오기
    history = await _get_chat_history(session_id, db)

    # 5. LLM 메시지 구성 (시스템 + 히스토리 + 현재 질문)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"참고 문서:\n{context}\n\n질문: {question}\n\n위 문서 내용을 기반으로 답변해주세요."
    })

    # 6. LLM 호출
    answer = await call_ollama_chat(messages=messages)

    # 7. 메시지 저장
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=question,
    )
    db.add(user_msg)

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=answer,
        sources={"documents": sources},
    )
    db.add(assistant_msg)

    # 세션 제목 업데이트 (첫 질문이면)
    if session.title == "새 대화":
        session.title = question[:50] + ("..." if len(question) > 50 else "")

    await db.commit()
    await db.refresh(assistant_msg)

    return {
        "answer": answer,
        "sources": sources,
        "message_id": assistant_msg.id,
    }


async def _build_rag_context(question: str, db: AsyncSession) -> tuple[str, list]:
    """질문에 대한 RAG 컨텍스트 생성 (retriever 사용)"""
    chunks = await retrieve_relevant_chunks(question, db)

    context_parts = []
    sources = []
    seen_docs = set()

    for chunk in chunks:
        context_parts.append(f"[{chunk['filename']} - 청크 {chunk['chunk_index'] + 1}]\n{chunk['content']}")

        if chunk['document_id'] not in seen_docs:
            sources.append({
                "document_id": chunk['document_id'],
                "filename": chunk['filename'],
                "relevance_score": chunk['score'],
            })
            seen_docs.add(chunk['document_id'])

    context = "\n\n---\n\n".join(context_parts) if context_parts else "관련 문서를 찾을 수 없습니다."
    return context, sources


async def ask_question_stream(
    question: str, session_id: str, user_id: str, db: AsyncSession
) -> AsyncGenerator[dict, None]:
    """RAG 기반 질문응답 (스트리밍)"""

    # 세션 확인
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        yield {"type": "error", "content": "채팅 세션을 찾을 수 없습니다"}
        return

    # RAG 컨텍스트 생성
    context, sources = await _build_rag_context(question, db)

    # 소스 먼저 전송
    yield {"type": "sources", "sources": sources}

    # 대화 히스토리 가져오기
    history = await _get_chat_history(session_id, db)

    # LLM 메시지 구성 (시스템 + 히스토리 + 현재 질문)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": f"참고 문서:\n{context}\n\n질문: {question}\n\n위 문서 내용을 기반으로 답변해주세요."
    })

    # LLM 스트리밍 호출
    full_answer = ""
    async for chunk in call_ollama_chat_stream(messages=messages):
        full_answer += chunk
        yield {"type": "token", "content": chunk}

    # 완료 신호
    yield {"type": "done", "content": full_answer}

    # 메시지 저장
    user_msg = ChatMessage(session_id=session_id, role="user", content=question)
    db.add(user_msg)

    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=full_answer,
        sources={"documents": sources},
    )
    db.add(assistant_msg)

    if session.title == "새 대화":
        session.title = question[:50] + ("..." if len(question) > 50 else "")

    await db.commit()


async def search_documents(query: str, db: AsyncSession, mode: str = "hybrid") -> list:
    """문서 검색 (키워드 + 벡터 하이브리드)"""
    results = []
    seen = set()

    # 1. 벡터 검색 (시맨틱)
    if mode in ("vector", "hybrid"):
        try:
            chunks = await retrieve_relevant_chunks(query, db, top_k=5)
            for chunk in chunks:
                if chunk['document_id'] not in seen:
                    # 검색어 주변 snippet 추출
                    content = chunk['content']
                    snippet = content[:200] if len(content) > 200 else content
                    results.append({
                        "document_id": chunk['document_id'],
                        "filename": chunk['filename'],
                        "content_snippet": snippet,
                        "score": chunk['score'],
                    })
                    seen.add(chunk['document_id'])
        except Exception as e:
            logger.warning(f"벡터 검색 실패 (키워드 검색으로 폴백): {e}")

    # 2. 키워드 검색 (파일명 + 내용)
    if mode in ("keyword", "hybrid"):
        keyword_query = select(
            DocumentChunk.document_id,
            DocumentChunk.content,
            Document.filename,
        ).join(Document).where(
            (Document.filename.ilike(f"%{query}%")) |
            (DocumentChunk.content.ilike(f"%{query}%"))
        ).where(Document.status == "completed").limit(10)

        result = await db.execute(keyword_query)
        rows = result.fetchall()

        for doc_id, content, filename in rows:
            if doc_id not in seen:
                # 검색어 주변 snippet 추출
                idx = content.lower().find(query.lower())
                if idx >= 0:
                    start = max(0, idx - 100)
                    end = min(len(content), idx + len(query) + 100)
                    snippet = content[start:end]
                else:
                    snippet = content[:200]

                results.append({
                    "document_id": doc_id,
                    "filename": filename,
                    "content_snippet": snippet,
                })
                seen.add(doc_id)

    return results
