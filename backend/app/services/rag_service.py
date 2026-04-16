"""
RAG Service - 질문응답 파이프라인
"""
import logging
import time
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document, DocumentChunk, ChatSession, ChatMessage, QueryLog
from app.services.llm_service import call_ollama_chat, call_ollama_chat_stream, call_ollama_embedding
from app.rag.retriever import retrieve_relevant_chunks
from app.config import get_settings
from app.services.guardrail_service import check_guardrail, PolicyAction

settings = get_settings()
logger = logging.getLogger("baikal.rag")

SYSTEM_PROMPT = """당신은 BAIKAL Private AI 시스템의 기업 내부 문서 전문 어시스턴트입니다.

## 답변 절차 (반드시 이 순서로 처리)
1. 제공된 참고 문서에서 질문과 관련된 내용을 먼저 찾는다.
2. 관련 내용이 있으면 그것만을 근거로 답변을 구성한다.
3. 관련 내용이 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다. 관련 문서를 추가로 업로드해 주세요."라고만 답한다.

## 핵심 규칙
1. **반드시 아래 제공된 참고 문서만을 근거로** 답변하세요. 문서 외의 지식을 사용하지 마세요.
2. 참고 문서 중 **질문과 직접 관련 없는 내용은 무시하고 포함하지 마세요**.
3. 이전 대화 내용을 요약하거나 반복하지 마세요. 오직 현재 질문에만 집중하세요.
4. 답변은 **항상 자연스럽고 명확한 한국어**로 작성하세요.
5. **핵심 내용을 먼저 1~2줄로 요약**한 후, 상세 내용을 구조화하여 설명하세요.
6. 숫자, 날짜, 금액 등 중요 수치는 **굵은 글씨**로 강조하세요.
7. 내용이 여러 항목이면 번호 목록이나 불릿을 사용하고, 비교 내용은 표로 정리하세요.
8. 답변 마지막에 "📄 출처: [문서명]" 형식으로 참고 문서를 명시하세요.
9. 질문이 모호하면 어떤 의도인지 되묻되, 가능한 해석이 하나라면 그대로 답변하세요."""

async def _save_guardrail_violation_log(
    user_id: str, question: str, session_id: str, guard, db: AsyncSession
) -> None:
    """Guardrail 차단 이벤트를 QueryLog에 기록 (feedback_score=-2)"""
    try:
        vio_log = QueryLog(
            user_id=user_id,
            query=question,
            response_summary=f"[GUARDRAIL:{guard.category}] {guard.reason}",
            confidence_score=0.0,
            latency_ms=0,
            session_id=session_id,
            model_name=settings.LLM_MODEL,
            feedback_score=-2,  # -2 = Policy Violation
        )
        db.add(vio_log)
        await db.commit()
    except Exception as e:
        logger.warning(f"Guardrail 로그 저장 실패: {e}")


async def _get_chat_history(session_id: str, db: AsyncSession) -> list[dict]:
    """세션의 최근 대화 히스토리를 가져옴"""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())
        .limit(settings.MAX_HISTORY_TURNS * 2)  # user+assistant 쌍
    )
    messages = result.scalars().all()
    # 시간순 정렬 (오래된 것부터)
    messages = list(reversed(messages))
    # 어시스턴트 답변은 500자로 제한 — 긴 이전 답변이 컨텍스트를 낭비하지 않도록
    result_msgs = []
    for m in messages:
        if m.role == "assistant" and len(m.content) > 500:
            content = m.content[:500] + "...(요약됨)"
        else:
            content = m.content
        result_msgs.append({"role": m.role, "content": content})
    return result_msgs


async def ask_question(
    question: str, session_id: str, user_id: str, db: AsyncSession,
    document_ids: list = None, user_role: str = "user",
    use_hyde: bool = False,
) -> dict:
    """RAG 기반 질문응답"""
    start_time = time.time()

    # 1. 세션 확인
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError("채팅 세션을 찾을 수 없습니다")

    # Guardrail: 비관련/유해 질문 선제 차단
    guard = check_guardrail(question, user_id=user_id)
    if guard.action != PolicyAction.ALLOW:
        await _save_guardrail_violation_log(user_id, question, session_id, guard, db)
        raise ValueError(guard.safe_message)

    # 2. RAG 컨텍스트 생성 (_build_rag_context 활용, 중복 로직 제거)
    context, sources, confidence_score, retriever_meta = await _build_rag_context(
        question, db, document_ids=document_ids, user_role=user_role, use_hyde=use_hyde
    )

    # 3. 대화 히스토리 가져오기
    history = await _get_chat_history(session_id, db)

    # 4. LLM 메시지 구성 (시스템 + 히스토리 + 현재 질문)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": (
            "[현재 질문 전용 참고 문서]\n"
            "아래 문서만 근거로 현재 질문에만 답변하세요. "
            "이전 답변 내용은 절대 요약하거나 반복하지 마세요.\n\n"
            f"{context}\n\n"
            f"질문: {question}"
        )
    })

    # 5. LLM 호출
    llm_start = time.time()
    answer = await call_ollama_chat(messages=messages)
    llm_ms = int((time.time() - llm_start) * 1000)

    latency_ms = int((time.time() - start_time) * 1000)

    # 6. 감사 로그 저장
    try:
        query_log = QueryLog(
            user_id=user_id,
            query=question,
            response_summary=answer[:500],
            document_ids=[s['document_id'] for s in sources],
            confidence_score=confidence_score,
            latency_ms=latency_ms,
            session_id=session_id,
            retrieved_chunks=retriever_meta.get("retrieved_chunks"),
            reranked_order=retriever_meta.get("reranked_order"),
            model_name=settings.LLM_MODEL,
            retrieval_ms=retriever_meta.get("retrieval_ms"),
            reranking_ms=retriever_meta.get("reranking_ms"),
            llm_ms=llm_ms,
        )
        db.add(query_log)
    except Exception as e:
        logger.warning(f"감사 로그 저장 실패: {e}")

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
        "confidence_score": confidence_score,
    }


async def _build_rag_context(
    question: str, db: AsyncSession,
    document_ids: list = None, user_role: str = "user",
    use_hyde: bool = False,
) -> tuple[str, list, float, dict]:
    """질문에 대한 RAG 컨텍스트 생성 (retriever 사용)
    반환: (context, sources, confidence_score, retriever_meta)
    """
    chunks, retriever_meta = await retrieve_relevant_chunks(
        question, db, document_ids=document_ids, user_role=user_role, use_hyde=use_hyde
    )

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
                "chunk_id": chunk.get('chunk_id'),
                "chunk_index": chunk['chunk_index'],
                "chunk_content": chunk['content'][:300],
                "page_number": chunk.get('page_number'),
            })
            seen_docs.add(chunk['document_id'])

    context = "\n\n---\n\n".join(context_parts) if context_parts else "관련 문서를 찾을 수 없습니다."
    if chunks:
        scores = sorted([c['score'] for c in chunks], reverse=True)
        top_score = scores[0]
        upper_half = scores[:max(1, len(scores) // 2)]
        upper_avg = sum(upper_half) / len(upper_half)
        confidence_score = round(0.6 * top_score + 0.4 * upper_avg, 3)
    else:
        confidence_score = 0.0
    return context, sources, confidence_score, retriever_meta


async def ask_question_stream(
    question: str, session_id: str, user_id: str, db: AsyncSession,
    document_ids: list = None, user_role: str = "user",
    use_hyde: bool = False,
) -> AsyncGenerator[dict, None]:
    """RAG 기반 질문응답 (스트리밍)"""
    start_time = time.time()

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

    # Guardrail: 비관련/유해 질문 선제 차단
    guard = check_guardrail(question, user_id=user_id)
    if guard.action != PolicyAction.ALLOW:
        await _save_guardrail_violation_log(user_id, question, session_id, guard, db)
        yield {"type": "error", "content": guard.safe_message}
        return

    # RAG 컨텍스트 생성
    context, sources, confidence_score, retriever_meta = await _build_rag_context(
        question, db, document_ids=document_ids, user_role=user_role, use_hyde=use_hyde
    )

    # 소스 먼저 전송
    yield {"type": "sources", "sources": sources}

    # 대화 히스토리 가져오기
    history = await _get_chat_history(session_id, db)

    # LLM 메시지 구성 (시스템 + 히스토리 + 현재 질문)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({
        "role": "user",
        "content": (
            "[현재 질문 전용 참고 문서]\n"
            "아래 문서만 근거로 현재 질문에만 답변하세요. "
            "이전 답변 내용은 절대 요약하거나 반복하지 마세요.\n\n"
            f"{context}\n\n"
            f"질문: {question}"
        )
    })

    # LLM 스트리밍 호출
    llm_start = time.time()
    full_answer = ""
    async for chunk in call_ollama_chat_stream(messages=messages):
        full_answer += chunk
        yield {"type": "token", "content": chunk}

    llm_ms = int((time.time() - llm_start) * 1000)
    latency_ms = int((time.time() - start_time) * 1000)

    # 완료 신호 전에 메시지 저장 → message_id 확보
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
    await db.refresh(assistant_msg)

    # 완료 신호 (신뢰도 점수 + message_id 포함)
    yield {"type": "done", "content": full_answer, "confidence_score": confidence_score, "message_id": assistant_msg.id}

    # 감사 로그 저장
    try:
        query_log = QueryLog(
            user_id=user_id,
            query=question,
            response_summary=full_answer[:500],
            document_ids=[s['document_id'] for s in sources],
            confidence_score=confidence_score,
            latency_ms=latency_ms,
            session_id=session_id,
            retrieved_chunks=retriever_meta.get("retrieved_chunks"),
            reranked_order=retriever_meta.get("reranked_order"),
            model_name=settings.LLM_MODEL,
            retrieval_ms=retriever_meta.get("retrieval_ms"),
            reranking_ms=retriever_meta.get("reranking_ms"),
            llm_ms=llm_ms,
        )
        db.add(query_log)
    except Exception as e:
        logger.warning(f"감사 로그 저장 실패: {e}")

    await db.commit()


async def search_documents(query: str, db: AsyncSession, mode: str = "hybrid") -> list:
    """문서 검색 (키워드 + 벡터 하이브리드)"""
    results = []
    seen = set()

    # 1. 벡터 검색 (시맨틱)
    if mode in ("vector", "hybrid"):
        try:
            chunks, _ = await retrieve_relevant_chunks(query, db, top_k=5)
            for chunk in chunks:
                if chunk['document_id'] not in seen:
                    # 검색어 주변 snippet 추출
                    content = chunk['content']
                    snippet = content[:200] if len(content) > 200 else content
                    results.append({
                        "document_id": chunk['document_id'],
                        "filename": chunk['filename'],
                        "content_snippet": snippet,
                        "content": content,
                        "score": chunk['score'],
                        "chunk_id": chunk.get('chunk_id'),
                        "chunk_index": chunk.get('chunk_index'),
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
                    "content": content,
                })
                seen.add(doc_id)

    return results
