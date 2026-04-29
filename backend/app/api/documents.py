"""
Documents API - 문서 관리
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, BackgroundTasks, Body
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.schemas.document import DocumentResponse, DocumentStatusResponse
from app.models.document import Document
from app.models.user import User
from app.core.deps import get_current_user, require_admin
from app.services.document_service import save_uploaded_file, process_document_async, delete_document

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.get("", response_model=List[DocumentResponse])
async def list_documents(
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(50, ge=1, le=200, description="최대 반환 수"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """문서 목록 조회 (페이지네이션 지원)"""
    if current_user.role == "admin":
        result = await db.execute(
            select(Document).order_by(Document.created_at.desc()).offset(skip).limit(limit)
        )
    else:
        result = await db.execute(
            select(Document)
            .where(Document.uploaded_by == current_user.id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
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
    current_user: User = Depends(get_current_user),
):
    """문서 처리 상태 조회"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    # 소유자 또는 관리자만 조회 가능 (IDOR 방지)
    if current_user.role != "admin" and doc.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")
    return doc


@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """문서 다운로드 (본인 업로드 또는 관리자만 허용)"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if current_user.role != "admin" and doc.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="이 문서에 접근할 권한이 없습니다")

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


@router.post("/{document_id}/retry", response_model=DocumentResponse)
async def retry_document_processing(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """실패/중단된 문서 재처리 (Stage 1.3)

    - failed 또는 처리 중 상태(processing) 둘 다 허용
    - completed 상태는 거부 (의도치 않은 재처리 방지 — 삭제 후 재업로드 사용)
    - 원본 파일이 디스크에 존재해야 함
    """
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if current_user.role != "admin" and doc.uploaded_by != current_user.id:
        raise HTTPException(status_code=403, detail="접근 권한이 없습니다")

    if doc.status == "completed":
        raise HTTPException(
            status_code=400,
            detail="이미 처리 완료된 문서입니다. 재처리하려면 삭제 후 다시 업로드하세요.",
        )

    import os as _os
    if not _os.path.exists(doc.filepath):
        raise HTTPException(
            status_code=410,
            detail="원본 파일이 서버에 존재하지 않습니다. 다시 업로드해주세요.",
        )

    # 상태를 uploading으로 되돌려 process_document_async가 정상 진입하도록 함
    doc.status = "uploading"
    doc.error_message = None
    doc.total_chunks = None
    doc.processed_chunks = None
    await db.commit()
    await db.refresh(doc)

    background_tasks.add_task(process_document_async, doc.id)
    return doc


@router.patch("/{document_id}/permissions")
async def update_document_permissions(
    document_id: str,
    is_public: Optional[bool] = Body(None),
    allowed_roles: Optional[List[str]] = Body(None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    """문서 접근 권한 설정 (Admin) — is_public / allowed_roles"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if is_public is not None:
        doc.is_public = is_public
    if allowed_roles is not None:
        valid_roles = [r for r in allowed_roles if r in ("admin", "manager", "user")]
        doc.allowed_roles = valid_roles if valid_roles else None

    await db.commit()
    await db.refresh(doc)
    return {
        "id": doc.id,
        "filename": doc.filename,
        "is_public": doc.is_public,
        "allowed_roles": doc.allowed_roles,
    }
