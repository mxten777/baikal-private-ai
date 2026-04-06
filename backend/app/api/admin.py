"""
Admin API - 시스템 설정 관리 (LLM 모델, 감사로그 등)
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
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
