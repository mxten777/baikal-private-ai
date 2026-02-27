"""
Documents API - 문서 관리
"""
import asyncio
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.models.document import Document
from app.models.user import User
from app.core.deps import get_current_user, require_admin
from app.services.document_service import save_uploaded_file, process_document_async, delete_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """문서 목록 조회"""
    if current_user.role == "admin":
        result = await db.execute(select(Document).order_by(Document.created_at.desc()))
    else:
        result = await db.execute(
            select(Document)
            .where(Document.uploaded_by == current_user.id)
            .order_by(Document.created_at.desc())
        )
    documents = result.scalars().all()
    return documents


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """문서 업로드 (비동기 처리)"""
    try:
        doc = await save_uploaded_file(file, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 비동기 백그라운드에서 문서 분석
    background_tasks.add_task(process_document_async, doc.id)

    return doc


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """문서 처리 상태 조회"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    return doc


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """문서 다운로드"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    return FileResponse(
        path=doc.filepath,
        filename=doc.filename,
        media_type="application/octet-stream",
    )


@router.delete("/{document_id}", status_code=204)
async def remove_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """문서 삭제 (Admin)"""
    success = await delete_document(document_id, db)
    if not success:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
