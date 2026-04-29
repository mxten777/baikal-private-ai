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

SYSTEM_PROMPT = """당신은 BAIKAL Private AI 시스템의 기업·공공기관 내부 문서 전문 어시스턴트입니다.
법령·조례·규정·예규 등 공식 문서를 다루며, **한 항목이라도 빠뜨리면 실무 사고로 이어지는 도메인**임을 인지하고 답변합니다.

## ⛔ 절대 규칙 — 다음 경우는 무조건 거절문구로만 답변
다음에 해당하는 질문은 참고 문서 유사도가 높게 보이더라도 **절대 답변을 생성하지 말고**, 정확히 다음 문장만 출력하세요:
"제공된 문서에서 해당 정보를 찾을 수 없습니다. 관련 문서를 추가로 업로드해 주세요."

거절 대상:
1. 외국·타국 사례 질문 (예: "미국의…", "일본의…", "해외에서는…", "다른 나라의…")
2. 가상·미래 시점 질문 (예: "다음 분기 예산은?", "내년에는?", "작년 통계는?")
3. 참고 문서에 명시되지 않은 개인정보 (예: 부서장·직원 이름, 주민등록번호 처리 등)
4. 참고 문서 범위 밖의 외부 지식 (인터넷 검색, 일반 상식, 다른 도메인 법령)
5. 참고 문서가 비어 있거나 질문과 무관한 경우

## 답변 절차 (위 절대 규칙에 해당하지 않을 때만)
1. 제공된 참고 문서에서 질문과 관련된 내용을 모두 찾는다 (1개라도 누락 금지).
2. 관련 내용이 있으면 그것만을 근거로 답변을 구성한다.
3. 관련 내용이 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다. 관련 문서를 추가로 업로드해 주세요."라고만 답한다.

## 핵심 규칙
1. **반드시 아래 제공된 참고 문서만을 근거로** 답변하세요. 문서 외의 지식·추측을 사용하지 마세요.
2. 참고 문서 중 **질문과 직접 관련 없는 내용은 무시**하고 포함하지 마세요.
3. 이전 대화 내용을 요약하거나 반복하지 마세요. 오직 현재 질문에만 집중하세요.
4. 답변은 **항상 자연스럽고 명확한 한국어**로 작성하세요.
5. **핵심 결론을 먼저 1~2줄로 요약**한 후, 상세 내용을 구조화하여 설명하세요.
6. 숫자, 날짜, 금액, 기간 등 중요 수치는 **굵은 글씨**로 강조하세요.

## 법령·규정 답변 형식 (이 형식을 반드시 지킬 것)
- "사유는?", "종류는?", "예외는?", "절차는?" 등 **여러 항목이 있는 질문**에서는:
  - 참고 문서에서 발견된 **모든 항목을 빠짐없이** 번호 매겨 나열한다 (1., 2., 3., …).
  - 각 항목 끝에 **근거 조·항·호**를 명시한다. 예: `(법 제21조 제4항 제1호)`.
  - 문서에 N개 항목이 있으면 정확히 N개를 출력한다. **임의 요약·생략 금지**.
- "정의", "기간", "구성" 등 **단일 사실 질문**도 조항 번호를 함께 표기한다.
- 비교 질문은 표(Markdown table)로 정리하고 행마다 출처(법령명·조항)를 분리 표기한다.

## 출처 표기 (필수)
1. 본문 안에서 인용하는 문장 끝마다 `(문서명, 제○조)` 형식으로 조항을 표기한다.
2. 답변 마지막 줄에는 반드시 `📄 출처: [문서명1], [문서명2]` 형식으로 사용한 모든 문서를 나열한다.
3. **참고 문서에 없는 조항 번호를 추측해서 만들지 마세요**. 조항 번호가 문서에 명시돼 있지 않으면 표기를 생략한다.

## 거절·한계 표시
- 질문이 모호하면 어떤 의도인지 되묻되, 가능한 해석이 하나라면 그대로 답변하세요.
- 참고 문서에 일부만 있고 나머지는 없으면, 있는 부분만 답하고 마지막에 "※ 위 외 사유는 제공된 문서에서 확인되지 않습니다." 라고 명시한다."""

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


def _evaluate_confidence_gate(
    chunks: list, confidence_score: float
) -> tuple[bool, str]:
    """Confidence Gate: 검색 결과 신뢰도가 임계 미만이면 거절.
    반환: (passed, refusal_reason)
      - passed=True  : 정상 진행
      - passed=False : refusal_reason 에 따라 거절 응답 사용
    """
    # 1. 청크 자체가 없으면 거절
    if not chunks:
        return False, "no_chunks"

    # 2. 인용 강제 (REQUIRE_CITATION=True 시 chunk가 0개면 차단 — 위와 동일)
    #    citation 누락은 LLM 응답 후처리에서 추가 검증

    # 3. 최상위 청크 점수 하한
    top1 = max((c.get("score", 0.0) for c in chunks), default=0.0)
    if top1 < settings.MIN_TOP1_SCORE:
        return False, "low_top1_score"

    # 4. 가중 신뢰도 하한
    if confidence_score < settings.MIN_CONFIDENCE_THRESHOLD:
        return False, "low_confidence"

    return True, ""


async def _save_refusal_log(
    user_id: str, question: str, session_id: str,
    refusal_reason: str, confidence_score: float,
    sources: list, db: AsyncSession,
) -> None:
    """Confidence Gate 거절을 QueryLog에 기록 (feedback_score=-3)"""
    try:
        log = QueryLog(
            user_id=user_id,
            query=question,
            response_summary=f"[REFUSAL:{refusal_reason}]",
            document_ids=[s["document_id"] for s in sources] if sources else [],
            confidence_score=confidence_score,
            latency_ms=0,
            session_id=session_id,
            model_name=settings.LLM_MODEL,
            feedback_score=-3,  # -3 = Confidence Gate Refusal
        )
        db.add(log)
        await db.commit()
    except Exception as e:
        logger.warning(f"거절 로그 저장 실패: {e}")


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

    # 2-1. Confidence Gate: 신뢰도 임계 미달 시 LLM 호출 없이 거절
    chunks_for_gate = retriever_meta.get("chunks_for_gate", [])
    gate_passed, refusal_reason = _evaluate_confidence_gate(chunks_for_gate, confidence_score)
    if not gate_passed:
        await _save_refusal_log(
            user_id, question, session_id, refusal_reason,
            confidence_score, sources, db,
        )
        # 사용자 메시지/응답 메시지 저장 (UI 흐름 유지)
        user_msg = ChatMessage(session_id=session_id, role="user", content=question)
        db.add(user_msg)
        refusal_text = settings.REFUSAL_MESSAGE
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=refusal_text,
            sources={"documents": sources, "refusal_reason": refusal_reason},
        )
        db.add(assistant_msg)
        if session.title == "새 대화":
            session.title = question[:50] + ("..." if len(question) > 50 else "")
        await db.commit()
        await db.refresh(assistant_msg)
        return {
            "answer": refusal_text,
            "sources": sources,
            "message_id": assistant_msg.id,
            "confidence_score": confidence_score,
            "refusal_reason": refusal_reason,
        }

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
    # Confidence Gate가 원본 청크 점수에 접근할 수 있도록 메타에 포함
    retriever_meta = dict(retriever_meta) if retriever_meta else {}
    retriever_meta["chunks_for_gate"] = chunks
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

    # Confidence Gate: 신뢰도 임계 미달 시 LLM 스트리밍 없이 거절
    chunks_for_gate = retriever_meta.get("chunks_for_gate", [])
    gate_passed, refusal_reason = _evaluate_confidence_gate(chunks_for_gate, confidence_score)
    if not gate_passed:
        await _save_refusal_log(
            user_id, question, session_id, refusal_reason,
            confidence_score, sources, db,
        )
        # 메시지 저장
        user_msg = ChatMessage(session_id=session_id, role="user", content=question)
        db.add(user_msg)
        refusal_text = settings.REFUSAL_MESSAGE
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=refusal_text,
            sources={"documents": sources, "refusal_reason": refusal_reason},
        )
        db.add(assistant_msg)
        if session.title == "새 대화":
            session.title = question[:50] + ("..." if len(question) > 50 else "")
        await db.commit()
        await db.refresh(assistant_msg)
        # 스트리밍 클라이언트에는 sources → token(refusal text) → done 순으로 전달
        yield {"type": "sources", "sources": sources}
        yield {"type": "token", "content": refusal_text}
        yield {
            "type": "done",
            "content": refusal_text,
            "confidence_score": confidence_score,
            "message_id": assistant_msg.id,
            "refusal_reason": refusal_reason,
        }
        return

    # 사용자 질문은 sources yield 이전에 먼저 저장 — 클라이언트가 sources 직후 끊어도 히스토리 보존
    # (yield 후 다음 await에서 GeneratorExit가 발생하면 commit 스킵됨)
    user_msg = ChatMessage(session_id=session_id, role="user", content=question)
    db.add(user_msg)
    if session.title == "새 대화":
        session.title = question[:50] + ("..." if len(question) > 50 else "")
    await db.commit()
    logger.info(f"[STREAM] user_msg committed session={session_id} msg_id={user_msg.id}")

    # 소스 전송
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

    # LLM 스트리밍 호출 — 도중에 끊겨도 finally에서 부분 답변 저장
    llm_start = time.time()
    full_answer = ""
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content="",
        sources={"documents": sources},
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)
    logger.info(f"[STREAM] assistant_msg row created session={session_id} msg_id={assistant_msg.id}")

    stream_completed = False
    try:
        async for chunk in call_ollama_chat_stream(messages=messages):
            full_answer += chunk
            yield {"type": "token", "content": chunk}
        stream_completed = True
    finally:
        # 스트리밍이 정상 완료됐든 클라이언트 단절로 끊겼든 부분 답변까지는 저장
        try:
            assistant_msg.content = full_answer if stream_completed else (full_answer + "\n\n[응답이 중단되었습니다]")
            await db.commit()
            logger.info(f"[STREAM] finally commit done completed={stream_completed} len={len(full_answer)}")
        except Exception as e:
            logger.warning(f"부분 답변 저장 실패: {e}")

    if not stream_completed:
        # 클라이언트가 이미 끊어졌으므로 done 이벤트는 무의미하지만, 안전하게 함수 종료
        return

    llm_ms = int((time.time() - llm_start) * 1000)
    latency_ms = int((time.time() - start_time) * 1000)

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
