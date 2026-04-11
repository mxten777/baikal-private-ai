"""
Retriever - 하이브리드 검색 (Vector + BM25) + Cross-encoder Reranking
P3-3: HyDE (Hypothetical Document Embeddings) 고정확도 검색 모드 추가
"""
import asyncio
import math
import logging
import time
from functools import lru_cache
from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text
from app.services.llm_service import call_ollama_embedding
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("baikal.retriever")


@lru_cache(maxsize=1)
def _get_cross_encoder():
    """Cross-encoder 모델 싱글턴 (최초 1회만 로드)"""
    try:
        from sentence_transformers import CrossEncoder
        model = CrossEncoder(settings.CROSS_ENCODER_MODEL)
        logger.info(f"Cross-encoder 로드 완료: {settings.CROSS_ENCODER_MODEL}")
        return model
    except Exception as e:
        logger.warning(f"Cross-encoder 로드 실패, MMR fallback 사용: {e}")
        return None


def _bm25_score(query_tokens: List[str], doc_tokens: List[str],
                avgdl: float, idf_map: dict,
                k1: float = 1.5, b: float = 0.75) -> float:
    """BM25 점수 계산 (단일 문서)"""
    score = 0.0
    doc_len = len(doc_tokens)
    tf_map: dict = {}
    for t in doc_tokens:
        tf_map[t] = tf_map.get(t, 0) + 1

    for token in query_tokens:
        tf = tf_map.get(token, 0)
        if tf == 0:
            continue
        idf = idf_map.get(token, 0.0)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / max(avgdl, 1))
        score += idf * (numerator / denominator)
    return score


def _compute_idf(corpus: List[List[str]]) -> dict:
    """후보 문서 집합 기반 IDF 계산 (BM25 표준식)"""
    N = len(corpus)
    df: dict = {}
    for doc_tokens in corpus:
        for token in set(doc_tokens):  # 문서별 중복 제거
            df[token] = df.get(token, 0) + 1
    idf_map = {}
    for token, freq in df.items():
        # Robertson IDF (음수 방지 처리 포함)
        idf_map[token] = math.log((N - freq + 0.5) / (freq + 0.5) + 1)
    return idf_map


def _tokenize(text: str) -> List[str]:
    """간단한 한국어/영어 토크나이저"""
    import re
    text = text.lower()
    # 한국어 2-gram + 영어 단어 분리
    tokens = re.findall(r'[가-힣]{2,}|[a-z0-9]+', text)
    # 한국어 2-gram 추가
    korean = re.findall(r'[가-힣]+', text)
    for word in korean:
        tokens += [word[i:i+2] for i in range(len(word) - 1)]
    return tokens


def _mmr_rerank(candidates: List[dict], top_k: int, lambda_val: float = 0.6) -> List[dict]:
    """MMR (Maximal Marginal Relevance) - 관련성과 다양성 균형"""
    if not candidates:
        return []

    selected = []
    remaining = list(candidates)

    while remaining and len(selected) < top_k:
        if not selected:
            # 첫 번째는 가장 높은 점수 선택
            best = max(remaining, key=lambda x: x["hybrid_score"])
        else:
            # MMR: 관련성 - 이미 선택된 것과의 텍스트 중복도
            def mmr_score(cand):
                relevance = cand["hybrid_score"]
                max_sim = 0.0
                cand_tokens = set(_tokenize(cand["content"]))
                for sel in selected:
                    sel_tokens = set(_tokenize(sel["content"]))
                    union = len(cand_tokens | sel_tokens)
                    if union > 0:
                        overlap = len(cand_tokens & sel_tokens) / union
                        max_sim = max(max_sim, overlap)
                return lambda_val * relevance - (1 - lambda_val) * max_sim

            best = max(remaining, key=mmr_score)

        selected.append(best)
        remaining.remove(best)

    return selected


async def _generate_hyde_document(query: str) -> str:
    """P3-3: HyDE — 질문에 대한 가상의 답변 문서 생성 (LLM 1차 호출)
    생성된 문서를 임베딩하면 실제 문서 청크와 공간적으로 더 가까움.
    """
    from app.services.llm_service import call_ollama_chat
    hyde_prompt = [
        {
            "role": "system",
            "content": (
                "당신은 전문 문서 작성자입니다. "
                "주어진 질문에 대해 실제 기업 내부 문서에서 발췌한 것처럼 "
                "간결한 답변 단락(3~5문장)을 작성하세요. "
                "정확한 정보가 없어도 됩니다. 형식과 어조를 맞추는 것이 목적입니다."
            ),
        },
        {"role": "user", "content": f"질문: {query}"},
    ]
    try:
        return await call_ollama_chat(hyde_prompt)
    except Exception as e:
        logger.warning(f"HyDE 문서 생성 실패, 원본 쿼리 사용: {e}")
        return query


async def retrieve_relevant_chunks(
    query: str, db: AsyncSession, top_k: int = None,
    document_ids: list = None, user_role: str = "user",
    use_hyde: bool = False,
) -> Tuple[List[dict], dict]:
    """하이브리드 검색 (Vector + BM25) + Cross-encoder Reranking
    document_ids: None이면 접근 가능한 전체 문서, 리스트면 해당 문서만 검색
    user_role: 문서 권한 필터링용
    반환값: (chunk 목록, 메타데이터 dict)
      메타데이터: retrieval_ms, reranking_ms, retrieved_chunks, reranked_order
    """
    if top_k is None:
        top_k = settings.TOP_K

    retrieval_start = time.time()

    # P3-3 HyDE: 가상 문서 생성 후 임베딩 (use_hyde=True 시)
    embedding_text = query
    if use_hyde:
        logger.info("HyDE 모드: 가상 답변 문서 생성 중...")
        embedding_text = await _generate_hyde_document(query)
        logger.debug(f"HyDE 문서: {embedding_text[:120]}")

    # 1단계: 질문(또는 HyDE 문서) 임베딩
    embeddings = await call_ollama_embedding([embedding_text])
    query_embedding = embeddings[0]
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # 2단계: 벡터 검색 - 후보 더 많이 가져오기 (top_k * 3)
    candidate_k = min(top_k * 3, 20)

    # 권한 필터: is_public=true OR allowed_roles에 user_role 포함
    # jsonb ? text : 배열 원소 존재 여부 확인
    doc_filter = """
        AND (d.is_public = true
             OR d.allowed_roles IS NULL
             OR d.allowed_roles::jsonb ? :user_role)
    """
    id_filter = ""
    params: dict = {"embedding": embedding_str, "top_k": candidate_k, "user_role": user_role}

    if document_ids:
        placeholders = ", ".join(f":did_{i}" for i in range(len(document_ids)))
        id_filter = f"AND dc.document_id IN ({placeholders})"
        for i, did in enumerate(document_ids):
            params[f"did_{i}"] = did

    search_query = sql_text(f"""
        SELECT dc.id, dc.content, dc.document_id, dc.chunk_index,
               dc.page_number, dc.source_type,
               d.filename,
               dc.embedding <=> CAST(:embedding AS vector) AS distance
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.status = 'completed'
        {doc_filter}
        {id_filter}
        ORDER BY dc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(search_query, params)
    rows = result.fetchall()

    if not rows:
        return [], {"retrieval_ms": int((time.time() - retrieval_start) * 1000), "reranking_ms": 0,
                    "retrieved_chunks": [], "reranked_order": []}

    # 3단계: 유사도 임계값 필터링
    candidates = []
    for row in rows:
        chunk_id, content, doc_id, chunk_index, page_number, source_type, filename, distance = row
        vector_score = round(1 - distance, 4)
        if vector_score >= settings.SIMILARITY_THRESHOLD:
            candidates.append({
                "chunk_id": chunk_id,
                "content": content,
                "document_id": doc_id,
                "chunk_index": chunk_index,
                "filename": filename,
                "page_number": page_number,
                "source_type": source_type,
                "vector_score": vector_score,
            })

    if not candidates:
        return [], {"retrieval_ms": int((time.time() - retrieval_start) * 1000), "reranking_ms": 0,
                    "retrieved_chunks": [], "reranked_order": []}

    # 4단계: BM25 점수 계산
    query_tokens = _tokenize(query)
    all_tokens = [_tokenize(c["content"]) for c in candidates]
    avgdl = sum(len(t) for t in all_tokens) / max(len(all_tokens), 1)
    idf_map = _compute_idf(all_tokens)

    bm25_scores = [
        _bm25_score(query_tokens, doc_tokens, avgdl, idf_map)
        for doc_tokens in all_tokens
    ]

    # BM25 정규화 (0~1)
    max_bm25 = max(bm25_scores) if bm25_scores else 1.0
    if max_bm25 > 0:
        bm25_scores = [s / max_bm25 for s in bm25_scores]

    # 5단계: 하이브리드 점수 합산 (벡터 70% + BM25 30%)
    for i, cand in enumerate(candidates):
        cand["bm25_score"] = round(bm25_scores[i], 4)
        cand["hybrid_score"] = round(
            0.7 * cand["vector_score"] + 0.3 * cand["bm25_score"], 4
        )

    # 6단계: MMR Reranking으로 다양하고 관련성 높은 top_k 선택
    mmr_results = _mmr_rerank(candidates, min(top_k * 2, len(candidates)))

    # 7단계: MMR 후 최종 점수 하한 필터 (관련 없는 청크 제거)
    mmr_results = [r for r in mmr_results if r["hybrid_score"] >= settings.MIN_HYBRID_SCORE]

    # 검색단계 완료 — retrieval_ms 확정
    retrieval_ms = int((time.time() - retrieval_start) * 1000)

    # 검색 단계 결과 기록 (KPI: retrieved_chunks)
    retrieved_chunks_meta = [
        {"chunk_id": r["chunk_id"], "score": r["hybrid_score"], "rank": i + 1}
        for i, r in enumerate(mmr_results)
    ]

    # 8단계: Cross-encoder Reranking (MMR 결과를 정밀 재정렬)
    reranking_start = time.time()
    cross_encoder = _get_cross_encoder()
    if cross_encoder is not None and mmr_results:
        try:
            pairs = [[query, r["content"]] for r in mmr_results]
            ce_scores = await asyncio.get_running_loop().run_in_executor(
                None, cross_encoder.predict, pairs
            )
            for i, r in enumerate(mmr_results):
                r["ce_score"] = float(ce_scores[i])
            mmr_results.sort(key=lambda x: x["ce_score"], reverse=True)
            final_results = mmr_results[:top_k]
            # 노출용 점수: sigmoid 변환으로 절대 관련도 반영
            # ce_score는 보통 -10 ~ +10 범위. sigmoid(x) = 1/(1+e^-x)
            for r in final_results:
                r["score"] = round(1 / (1 + math.exp(-r["ce_score"])), 4)
            logger.info(
                f"검색 완료: 후보 {len(candidates)}개 → MMR {len(mmr_results)}개 "
                f"→ Cross-encoder top{len(final_results)}"
            )
        except Exception as e:
            logger.warning(f"Cross-encoder 실패, hybrid_score 순 fallback: {e}")
            final_results = mmr_results[:top_k]
            for r in final_results:
                r["score"] = r["hybrid_score"]
    else:
        final_results = mmr_results[:top_k]
        for r in final_results:
            r["score"] = r["hybrid_score"]
        logger.info(
            f"검색 완료: 후보 {len(candidates)}개 → MMR 선택 {len(final_results)}개 "
            f"(벡터70%+BM25 30%)"
        )

    reranking_ms = int((time.time() - reranking_start) * 1000)
    reranked_order = [r["chunk_id"] for r in final_results]

    meta = {
        "retrieval_ms": retrieval_ms,
        "reranking_ms": reranking_ms,
        "retrieved_chunks": retrieved_chunks_meta,
        "reranked_order": reranked_order,
    }
    return final_results, meta

