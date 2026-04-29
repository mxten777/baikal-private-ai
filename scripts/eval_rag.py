"""
P3-2: RAG 평가 스크립트
Precision@K, Recall@K, MRR, nDCG@K, Reranking Lift 자동 산출

사용법:
  python scripts/eval_rag.py --testset scripts/eval_testset.json [--k 5] [--mode hybrid]

환경 변수 (.env 파일 또는 직접 설정):
  DATABASE_URL, OLLAMA_BASE_URL, LLM_MODEL, EMBEDDING_MODEL 등
"""
import asyncio
import json
import math
import argparse
import sys
import os
from pathlib import Path

# 프로젝트 루트 → sys.path에 추가
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "backend"))

# .env 로드
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import get_settings
from app.rag.retriever import retrieve_relevant_chunks

settings = get_settings()

# ── 지표 계산 함수 ────────────────────────────────────────────

def precision_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float:
    """Precision@K: 상위 K개 중 관련 청크 문서 비율."""
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return hits / k if k > 0 else 0.0


def recall_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float:
    """Recall@K: 정답 문서가 상위 K 안에 포함된 비율."""
    if not relevant_ids:
        return 0.0
    top_k = set(retrieved_ids[:k])
    hits = sum(1 for doc_id in relevant_ids if doc_id in top_k)
    return hits / len(relevant_ids)


def mrr(retrieved_ids: list, relevant_ids: list) -> float:
    """MRR: 최초 정답이 몇 번째 순위에 등장하는지 역수."""
    for rank, doc_id in enumerate(retrieved_ids, start=1):
        if doc_id in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: list, relevant_ids: list, k: int) -> float:
    """nDCG@K: 순위 가중 품질 평가."""
    def dcg(ids: list, k: int) -> float:
        score = 0.0
        for i, doc_id in enumerate(ids[:k], start=1):
            rel = 1.0 if doc_id in relevant_ids else 0.0
            score += rel / math.log2(i + 1)
        return score

    actual_dcg = dcg(retrieved_ids, k)
    ideal_ids = [doc_id for doc_id in retrieved_ids if doc_id in relevant_ids] + \
                [doc_id for doc_id in retrieved_ids if doc_id not in relevant_ids]
    ideal_dcg = dcg(ideal_ids, k)
    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


def reranking_lift(pre_rerank_ids: list, post_rerank_ids: list,
                   relevant_ids: list, k: int) -> float:
    """Reranking Lift: Cross-encoder 적용 전후 Precision@K 개선폭."""
    pre = precision_at_k(pre_rerank_ids, relevant_ids, k)
    post = precision_at_k(post_rerank_ids, relevant_ids, k)
    return round(post - pre, 4)


def keyword_match_score(answer: str, expected_keywords: list) -> float:
    """답변 내 예상 키워드 포함 비율 (Citation Accuracy proxy)."""
    if not expected_keywords:
        return 1.0
    answer_lower = answer.lower()
    hits = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
    return hits / len(expected_keywords)


# ── 평가 메인 로직 ─────────────────────────────────────────────

async def evaluate_query(
    query: str,
    relevant_doc_ids: list,
    expected_keywords: list,
    db: AsyncSession,
    k: int,
) -> dict:
    """단일 쿼리 평가. 반환: 각종 지표 dict."""
    try:
        chunks, meta = await retrieve_relevant_chunks(query, db, top_k=k)
    except Exception as e:
        return {"error": str(e)}

    retrieved_doc_ids = [c["document_id"] for c in chunks]
    retrieved_chunk_ids = [c["chunk_id"] for c in chunks]

    # MMR 전 후보 순서 추출 (retrieved_chunks metafield)
    # retrieved_chunks는 MMR 후 순서이므로 그대로 사용 (Lift는 reranked_order와 비교)
    pre_rerank_ids = []
    if meta.get("retrieved_chunks"):
        # retrieved_chunks: MMR 전 후보 목록 (chunk_id 기반) → document_id로 변환 필요
        # chunk_id별로 document_id가 없으므로, retrieved chunk의 doc_id 순서로 근사
        # 실용적 대안: retrieved_chunks 순서 vs reranked_order 순서로 문서 Precision 비교
        rc_order = [rc["chunk_id"] for rc in meta["retrieved_chunks"]]
        pre_rerank_doc_ids = []
        chunk_to_doc = {c["chunk_id"]: c["document_id"] for c in chunks}
        for cid in rc_order:
            doc_id = chunk_to_doc.get(cid)
            if doc_id and doc_id not in pre_rerank_doc_ids:
                pre_rerank_doc_ids.append(doc_id)
        pre_rerank_ids = pre_rerank_doc_ids

    lift = reranking_lift(
        pre_rerank_ids or retrieved_doc_ids,
        retrieved_doc_ids,
        relevant_doc_ids,
        k,
    )

    return {
        "retrieved_doc_ids": retrieved_doc_ids,
        "retrieved_chunk_ids": retrieved_chunk_ids,
        "precision_at_k": round(precision_at_k(retrieved_doc_ids, relevant_doc_ids, k), 4),
        "recall_at_k": round(recall_at_k(retrieved_doc_ids, relevant_doc_ids, k), 4),
        "mrr": round(mrr(retrieved_doc_ids, relevant_doc_ids), 4),
        "ndcg_at_k": round(ndcg_at_k(retrieved_doc_ids, relevant_doc_ids, k), 4),
        "reranking_lift": lift,
        "retrieval_ms": meta.get("retrieval_ms", 0),
        "reranking_ms": meta.get("reranking_ms", 0),
    }


async def run_evaluation(testset_path: str, k: int, md_output: str = None):
    """전체 테스트셋 평가 실행."""    # 테스트셋 로드
    with open(testset_path, "r", encoding="utf-8") as f:
        testset = json.load(f)

    print(f"\n{'='*60}")
    print(f"  BAIKAL RAG 평가 | k={k} | 테스트셋: {len(testset)}건")
    print(f"{'='*60}\n")

    # DB 세션 생성
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results = []
    async with Session() as db:
        for i, item in enumerate(testset, start=1):
            query = item["query"]
            relevant_doc_ids = item.get("relevant_doc_ids", [])
            expected_keywords = item.get("expected_keywords", [])
            query_type = item.get("query_type", "general")

            print(f"[{i:02d}/{len(testset)}] {query_type}: {query[:60]}...")
            result = await evaluate_query(query, relevant_doc_ids, expected_keywords, db, k)

            if "error" in result:
                print(f"       ❌ 오류: {result['error']}")
                continue

            result.update({
                "query": query,
                "query_type": query_type,
                "relevant_doc_ids": relevant_doc_ids,
            })
            results.append(result)

            # 개별 결과 출력
            p = result["precision_at_k"]
            r = result["recall_at_k"]
            m = result["mrr"]
            n = result["ndcg_at_k"]
            lift = result["reranking_lift"]
            print(f"       P@{k}={p:.3f}  R@{k}={r:.3f}  MRR={m:.3f}  nDCG@{k}={n:.3f}  Lift={lift:+.3f}")
            print(f"       Retrieval={result['retrieval_ms']}ms  Reranking={result['reranking_ms']}ms")

    await engine.dispose()

    if not results:
        print("\n평가 결과가 없습니다. 테스트셋을 확인해주세요.")
        return

    # ── 집계 ──────────────────────────────────────────────────
    n = len(results)
    avg = lambda key: sum(r[key] for r in results) / n

    print(f"\n{'='*60}")
    print(f"  집계 결과 (n={n})")
    print(f"{'='*60}")
    print(f"  Precision@{k:<3}  : {avg('precision_at_k'):.4f}  (목표: ≥0.80)")
    print(f"  Recall@{k:<5}    : {avg('recall_at_k'):.4f}")
    print(f"  MRR              : {avg('mrr'):.4f}")
    print(f"  nDCG@{k:<5}      : {avg('ndcg_at_k'):.4f}")
    print(f"  Reranking Lift   : {avg('reranking_lift'):+.4f}")
    print(f"  Avg Retrieval ms : {avg('retrieval_ms'):.0f}  (목표: ≤1500ms)")
    print(f"  Avg Reranking ms : {avg('reranking_ms'):.0f}  (목표: ≤500ms)")

    # 목표 달성 여부
    print(f"\n  목표 달성 여부:")
    p_avg = avg('precision_at_k')
    r_avg = avg('retrieval_ms')
    rr_avg = avg('reranking_ms')
    print(f"  {'✅' if p_avg >= 0.80 else '❌'} Precision@{k} ≥ 0.80  → {p_avg:.4f}")
    print(f"  {'✅' if r_avg <= 1500 else '❌'} Retrieval ≤ 1500ms → {r_avg:.0f}ms")
    print(f"  {'✅' if rr_avg <= 500 else '❌'} Reranking ≤ 500ms  → {rr_avg:.0f}ms")

    # 쿼리 유형별 분석
    query_types = list(set(r["query_type"] for r in results))
    if len(query_types) > 1:
        print(f"\n  쿼리 유형별 Precision@{k}:")
        for qt in sorted(query_types):
            type_results = [r for r in results if r["query_type"] == qt]
            type_avg = sum(r["precision_at_k"] for r in type_results) / len(type_results)
            print(f"    {qt:<15}: {type_avg:.4f}  (n={len(type_results)})")

    print(f"\n{'='*60}\n")

    # 결과 파일 저장
    output_path = Path(testset_path).parent / "eval_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "k": k,
            "n": n,
            "summary": {
                "precision_at_k": round(avg('precision_at_k'), 4),
                "recall_at_k": round(avg('recall_at_k'), 4),
                "mrr": round(avg('mrr'), 4),
                "ndcg_at_k": round(avg('ndcg_at_k'), 4),
                "reranking_lift": round(avg('reranking_lift'), 4),
                "avg_retrieval_ms": round(avg('retrieval_ms'), 1),
                "avg_reranking_ms": round(avg('reranking_ms'), 1),
            },
            "details": results,
        }, f, ensure_ascii=False, indent=2)
    print(f"  결과 저장: {output_path}\n")

    # ── 마크다운 리포트 (선택) ──────────────────────────────────
    if md_output:
        from datetime import datetime
        md_path = Path(md_output)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        p_avg = avg('precision_at_k')
        r_avg_ms = avg('retrieval_ms')
        rr_avg_ms = avg('reranking_ms')
        lines = []
        lines.append(f"# BAIKAL RAG 평가 리포트")
        lines.append("")
        lines.append(f"- 측정일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        lines.append(f"- 테스트셋: `{testset_path}` (n={n})")
        lines.append(f"- K = {k}")
        lines.append("")
        lines.append("## 핵심 지표")
        lines.append("")
        lines.append("| 지표 | 측정값 | 목표 | 달성 |")
        lines.append("|------|-------:|-----:|:----:|")
        lines.append(f"| Precision@{k} | {p_avg:.4f} | ≥ 0.80 | {'✅' if p_avg >= 0.80 else '❌'} |")
        lines.append(f"| Recall@{k}    | {avg('recall_at_k'):.4f} | – | – |")
        lines.append(f"| MRR           | {avg('mrr'):.4f} | – | – |")
        lines.append(f"| nDCG@{k}      | {avg('ndcg_at_k'):.4f} | – | – |")
        lines.append(f"| Reranking Lift| {avg('reranking_lift'):+.4f} | > 0 | {'✅' if avg('reranking_lift') > 0 else '❌'} |")
        lines.append(f"| Avg Retrieval | {r_avg_ms:.0f} ms | ≤ 1500 ms | {'✅' if r_avg_ms <= 1500 else '❌'} |")
        lines.append(f"| Avg Reranking | {rr_avg_ms:.0f} ms | ≤ 500 ms | {'✅' if rr_avg_ms <= 500 else '❌'} |")
        lines.append("")
        # 쿼리 유형별
        query_types = sorted(set(r["query_type"] for r in results))
        if len(query_types) > 1:
            lines.append(f"## 쿼리 유형별 Precision@{k}")
            lines.append("")
            lines.append("| 유형 | n | Precision |")
            lines.append("|------|--:|----------:|")
            for qt in query_types:
                tr = [r for r in results if r["query_type"] == qt]
                lines.append(f"| {qt} | {len(tr)} | {sum(r['precision_at_k'] for r in tr)/len(tr):.4f} |")
            lines.append("")
        lines.append("## 개별 쿼리 결과")
        lines.append("")
        lines.append(f"| # | 유형 | Query | P@{k} | R@{k} | MRR | nDCG@{k} | Lift |")
        lines.append("|--:|------|-------|------:|------:|----:|---------:|-----:|")
        for i, r in enumerate(results, 1):
            q = r["query"][:60].replace("|", "/")
            lines.append(
                f"| {i} | {r['query_type']} | {q} | {r['precision_at_k']:.3f} | "
                f"{r['recall_at_k']:.3f} | {r['mrr']:.3f} | "
                f"{r['ndcg_at_k']:.3f} | {r['reranking_lift']:+.3f} |"
            )
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*이 리포트는 `scripts/eval_rag.py --output md` 으로 자동 생성되었습니다.*")
        md_path.write_text("\n".join(lines), encoding="utf-8")
        print(f"  마크다운 리포트: {md_path}\n")


def main():
    parser = argparse.ArgumentParser(description="BAIKAL RAG 평가 스크립트")
    parser.add_argument("--testset", default="scripts/eval_testset.json",
                        help="테스트셋 JSON 파일 경로")
    parser.add_argument("--k", type=int, default=5,
                        help="Precision@K, Recall@K, nDCG@K의 K값 (기본: 5)")
    parser.add_argument("--output", default=None,
                        help="마크다운 리포트 출력 경로. 'md'면 docs/TEST_RESULTS.md 사용")
    args = parser.parse_args()

    if not os.path.exists(args.testset):
        print(f"❌ 테스트셋 파일 없음: {args.testset}")
        print("   scripts/eval_testset.json 을 먼저 작성하세요.")
        sys.exit(1)

    md_output = None
    if args.output:
        md_output = "docs/TEST_RESULTS.md" if args.output == "md" else args.output

    asyncio.run(run_evaluation(args.testset, args.k, md_output=md_output))


if __name__ == "__main__":
    main()
