"""
Admin API - 시스템 설정 관리 (LLM 모델, 감사로그 등)
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
import httpx
from app.database import get_db
from app.models.document import QueryLog
from app.models.user import User
from app.core.deps import require_admin
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("baikal.admin")
router = APIRouter(prefix="/api/admin", tags=["admin"])


# ── LLM 모델 관리 ─────────────────────────────────────────────

@router.get("/models")
async def list_ollama_models(_admin: User = Depends(require_admin)):
    """Ollama에서 사용 가능한 모델 목록 조회"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            res.raise_for_status()
            data = res.json()
            models = [
                {
                    "name": m["name"],
                    "size": m.get("size", 0),
                    "modified_at": m.get("modified_at", ""),
                    "is_current": m["name"] == settings.LLM_MODEL,
                }
                for m in data.get("models", [])
            ]
            return {
                "models": models,
                "current_model": settings.LLM_MODEL,
                "embedding_model": settings.EMBEDDING_MODEL,
            }
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail="Ollama 서버에 연결할 수 없습니다")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/models/activate")
async def activate_model(
    model_name: str,
    _admin: User = Depends(require_admin),
):
    """활성 LLM 모델 변경 (런타임, 재시작 전까지 유효)"""
    # 모델 존재 확인
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            res.raise_for_status()
            available = [m["name"] for m in res.json().get("models", [])]
    except Exception:
        raise HTTPException(status_code=503, detail="Ollama 서버에 연결할 수 없습니다")

    if model_name not in available:
        raise HTTPException(
            status_code=404,
            detail=f"모델 '{model_name}'이(가) Ollama에 없습니다. 먼저 'ollama pull {model_name}'을 실행하세요."
        )

    # 런타임 settings 객체 변경 (프로세스 내 유효)
    settings.LLM_MODEL = model_name
    logger.info(f"LLM 모델 변경: {model_name}")
    return {"message": f"활성 모델이 '{model_name}'으로 변경되었습니다", "model": model_name}


# ── 감사 로그 ─────────────────────────────────────────────────

@router.get("/query-logs")
async def list_query_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """질의 감사 로그 목록 (Admin)"""
    result = await db.execute(
        select(QueryLog)
        .order_by(desc(QueryLog.created_at))
        .offset(skip)
        .limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(log.id),
            "user_id": log.user_id,
            "query": log.query,
            "response_summary": log.response_summary,
            "document_ids": log.document_ids,
            "confidence_score": log.confidence_score,
            "latency_ms": log.latency_ms,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/query-logs/stats")
async def query_log_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """감사 로그 통계"""
    from sqlalchemy import func
    result = await db.execute(
        select(
            func.count(QueryLog.id).label("total"),
            func.avg(QueryLog.confidence_score).label("avg_confidence"),
            func.avg(QueryLog.latency_ms).label("avg_latency_ms"),
        )
    )
    row = result.one()
    return {
        "total_queries": row.total or 0,
        "avg_confidence": round(float(row.avg_confidence or 0), 3),
        "avg_latency_ms": round(float(row.avg_latency_ms or 0)),
    }


# ── P2-7: Active User Rate KPI ────────────────────────────────

@router.get("/kpi/active-users")
async def active_user_rate(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """최근 7일/30일 활성 사용자 수 및 비율 (P2-7 Active User Rate KPI)"""
    now = datetime.now(timezone.utc)
    day7 = now - timedelta(days=7)
    day30 = now - timedelta(days=30)

    # 전체 사용자 수
    total_result = await db.execute(
        select(func.count(User.id)).where(User.is_active == True)
    )
    total_users = total_result.scalar() or 0

    # 최근 7일 활성 사용자 (질의 기록 기준)
    wau_result = await db.execute(
        select(func.count(func.distinct(QueryLog.user_id)))
        .where(QueryLog.created_at >= day7)
    )
    wau = wau_result.scalar() or 0

    # 최근 30일 활성 사용자
    mau_result = await db.execute(
        select(func.count(func.distinct(QueryLog.user_id)))
        .where(QueryLog.created_at >= day30)
    )
    mau = mau_result.scalar() or 0

    return {
        "total_users": total_users,
        "wau": wau,
        "mau": mau,
        "wau_rate": round(wau / total_users * 100, 1) if total_users > 0 else 0.0,
        "mau_rate": round(mau / total_users * 100, 1) if total_users > 0 else 0.0,
    }


@router.get("/kpi/rag-performance")
async def rag_performance(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """RAG 단계별 성능 KPI (P2-2 응답 단계별 지연시간 + P2-3 신뢰도 분포)"""
    # 단계별 평균 지연시간
    perf_result = await db.execute(
        select(
            func.avg(QueryLog.retrieval_ms).label("avg_retrieval_ms"),
            func.avg(QueryLog.reranking_ms).label("avg_reranking_ms"),
            func.avg(QueryLog.llm_ms).label("avg_llm_ms"),
            func.avg(QueryLog.latency_ms).label("avg_total_ms"),
            func.count(QueryLog.id).label("total"),
        ).where(QueryLog.retrieval_ms != None)
    )
    perf = perf_result.one()

    # 신뢰도 분포  (High ≥0.7 / Medium 0.4~0.7 / Low <0.4)
    conf_result = await db.execute(
        select(
            func.count(QueryLog.id).filter(QueryLog.confidence_score >= 0.7).label("high"),
            func.count(QueryLog.id).filter(
                QueryLog.confidence_score >= 0.4, QueryLog.confidence_score < 0.7
            ).label("medium"),
            func.count(QueryLog.id).filter(QueryLog.confidence_score < 0.4).label("low"),
        ).where(QueryLog.confidence_score != None)
    )
    conf = conf_result.one()

    # 피드백 집계
    fb_result = await db.execute(
        select(
            func.count(QueryLog.id).filter(QueryLog.feedback_score == 1).label("positive"),
            func.count(QueryLog.id).filter(QueryLog.feedback_score == -1).label("negative"),
            func.count(QueryLog.id).filter(QueryLog.feedback_score != None).label("total_fb"),
        )
    )
    fb = fb_result.one()

    # 출처 클릭률
    click_result = await db.execute(
        select(
            func.count(QueryLog.id).filter(QueryLog.click_source_flag == True).label("clicked"),
            func.count(QueryLog.id).label("total_all"),
        )
    )
    click = click_result.one()

    return {
        "latency": {
            "avg_retrieval_ms": round(float(perf.avg_retrieval_ms or 0)),
            "avg_reranking_ms": round(float(perf.avg_reranking_ms or 0)),
            "avg_llm_ms": round(float(perf.avg_llm_ms or 0)),
            "avg_total_ms": round(float(perf.avg_total_ms or 0)),
            "sample_count": perf.total or 0,
        },
        "confidence_distribution": {
            "high": conf.high or 0,
            "medium": conf.medium or 0,
            "low": conf.low or 0,
        },
        "feedback": {
            "positive": fb.positive or 0,
            "negative": fb.negative or 0,
            "total": fb.total_fb or 0,
            "success_rate": round(
                fb.positive / fb.total_fb * 100, 1
            ) if fb.total_fb and fb.total_fb > 0 else 0.0,
        },
        "source_click_rate": round(
            click.clicked / click.total_all * 100, 1
        ) if click.total_all and click.total_all > 0 else 0.0,
    }


@router.get("/kpi/weekly-trend")
async def weekly_trend(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """최근 7일 일별 질의 수 + 평균 신뢰도 추이 (P2-1 대시보드 차트용)"""
    now = datetime.now(timezone.utc)
    trends = []
    for i in range(6, -1, -1):
        day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        row_result = await db.execute(
            select(
                func.count(QueryLog.id).label("count"),
                func.avg(QueryLog.confidence_score).label("avg_conf"),
            ).where(
                QueryLog.created_at >= day_start,
                QueryLog.created_at < day_end,
            )
        )
        row = row_result.one()
        trends.append({
            "date": day_start.strftime("%m/%d"),
            "count": row.count or 0,
            "avg_confidence": round(float(row.avg_conf or 0), 3),
        })
    return {"trends": trends}


@router.get("/kpi/policy-violations")
async def policy_violations(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """P3-1 Guardrail Engine: 정책 위반 카운트 및 최근 내역.
    feedback_score = -2 인 QueryLog 레코드가 차단된 질문.
    """
    # 총 위반 수
    total_result = await db.execute(
        select(func.count(QueryLog.id)).where(QueryLog.feedback_score == -2)
    )
    total = total_result.scalar() or 0

    # 오늘 위반 수
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_result = await db.execute(
        select(func.count(QueryLog.id)).where(
            QueryLog.feedback_score == -2,
            QueryLog.created_at >= today_start,
        )
    )
    today = today_result.scalar() or 0

    # 최근 10건 내역
    recent_result = await db.execute(
        select(QueryLog)
        .where(QueryLog.feedback_score == -2)
        .order_by(desc(QueryLog.created_at))
        .limit(10)
    )
    recent_logs = recent_result.scalars().all()
    recent = [
        {
            "id": log.id,
            "query": log.query[:100],
            "reason": log.response_summary,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in recent_logs
    ]

    return {
        "total_violations": total,
        "today_violations": today,
        "recent": recent,
    }
