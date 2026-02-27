"""
Search API - 문서 검색
"""
from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.schemas.document import SearchResult
from app.models.user import User
from app.core.deps import get_current_user
from app.services.rag_service import search_documents

router = APIRouter(prefix="/api/search", tags=["search"])


@router.get("", response_model=List[SearchResult])
async def search(
    q: str = Query(..., min_length=1, description="검색어"),
    mode: str = Query("hybrid", description="검색 모드: keyword, vector, hybrid"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """문서 검색 (키워드 + 벡터 하이브리드)"""
    if mode not in ("keyword", "vector", "hybrid"):
        mode = "hybrid"
    results = await search_documents(q, db, mode=mode)
    return results
