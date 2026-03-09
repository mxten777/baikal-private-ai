"""
Retriever - 하이브리드 검색 (Vector + BM25) + MMR Reranking
"""
import math
import logging
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text as sql_text
from app.services.llm_service import call_ollama_embedding
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("baikal.retriever")


def _bm25_score(query_tokens: List[str], doc_tokens: List[str],
                avgdl: float, k1: float = 1.5, b: float = 0.75) -> float:
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
        idf = math.log(1 + 1)  # 단순화된 IDF (전체 코퍼스 없이)
        numerator = tf * (k1 + 1)
        denominator = tf + k1 * (1 - b + b * doc_len / max(avgdl, 1))
        score += idf * (numerator / denominator)
    return score


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


async def retrieve_relevant_chunks(
    query: str, db: AsyncSession, top_k: int = None
) -> List[dict]:
    """하이브리드 검색 (Vector + BM25) + MMR Reranking"""
    if top_k is None:
        top_k = settings.TOP_K

    # 1단계: 질문 임베딩
    embeddings = await call_ollama_embedding([query])
    query_embedding = embeddings[0]
    embedding_str = "[" + ",".join(str(x) for x in query_embedding) + "]"

    # 2단계: 벡터 검색 - 후보 더 많이 가져오기 (top_k * 3)
    candidate_k = min(top_k * 3, 20)
    search_query = sql_text("""
        SELECT dc.id, dc.content, dc.document_id, dc.chunk_index,
               d.filename,
               dc.embedding <=> CAST(:embedding AS vector) AS distance
        FROM document_chunks dc
        JOIN documents d ON d.id = dc.document_id
        WHERE d.status = 'completed'
        ORDER BY dc.embedding <=> CAST(:embedding AS vector)
        LIMIT :top_k
    """)

    result = await db.execute(
        search_query,
        {"embedding": embedding_str, "top_k": candidate_k},
    )
    rows = result.fetchall()

    if not rows:
        return []

    # 3단계: 유사도 임계값 필터링
    candidates = []
    for row in rows:
        chunk_id, content, doc_id, chunk_index, filename, distance = row
        vector_score = round(1 - distance, 4)
        if vector_score >= settings.SIMILARITY_THRESHOLD:
            candidates.append({
                "chunk_id": chunk_id,
                "content": content,
                "document_id": doc_id,
                "chunk_index": chunk_index,
                "filename": filename,
                "vector_score": vector_score,
            })

    if not candidates:
        return []

    # 4단계: BM25 점수 계산
    query_tokens = _tokenize(query)
    all_tokens = [_tokenize(c["content"]) for c in candidates]
    avgdl = sum(len(t) for t in all_tokens) / max(len(all_tokens), 1)

    bm25_scores = [
        _bm25_score(query_tokens, doc_tokens, avgdl)
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
    final_results = _mmr_rerank(candidates, top_k)

    # 노출용 점수는 hybrid_score 사용
    for r in final_results:
        r["score"] = r["hybrid_score"]

    logger.info(
        f"검색 완료: 후보 {len(candidates)}개 → MMR 선택 {len(final_results)}개 "
        f"(벡터70%+BM25 30%)"
    )
    return final_results

