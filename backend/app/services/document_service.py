"""
Document Service - 파일 업로드, 관리, 비동기 처리
"""
import asyncio
import functools
import os
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document, DocumentChunk
from app.config import get_settings
from app.database import async_session
from app.rag.loader import extract_text, extract_pages, extract_pdf_with_vision, extract_docx_with_vision
from app.rag.chunker import (
    chunk_text, table_chunk_to_nl,
    split_into_paragraphs, semantic_chunk_with_embeddings,
    split_table_aware,
)
from app.rag.embedder import generate_embeddings

_utcnow = lambda: datetime.now(timezone.utc)

settings = get_settings()
logger = logging.getLogger("baikal.document")

ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "hwp", "hwpx"}
MIME_TO_EXT = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
    "application/x-hwp": "hwp",
    "application/haansofthwp": "hwp",
    "application/vnd.hancom.hwp": "hwp",
    "application/vnd.hancom.hwpx": "hwpx",
}


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _find_chunk_page(chunk_content: str, pages: List[Tuple]) -> Optional[int]:
    """청크 내용 첫 60자로 어느 페이지에 속하는지 탐색."""
    if not pages:
        return None
    search_key = chunk_content[:60].strip()
    if not search_key:
        return None
    for page_num, page_text in pages:
        if search_key in page_text:
            return page_num
    return None


def _detect_source_type(chunk_content: str) -> str:
    """청크 소스 타입 감지 — 탭 구분 표 비율로 판단."""
    lines = [ln for ln in chunk_content.split('\n') if ln.strip()]
    if not lines:
        return "text"
    table_lines = sum(1 for ln in lines if '\t' in ln and len(ln.split('\t')) >= 3)
    return "table" if table_lines >= max(len(lines) * 0.5, 1) else "text"


def validate_file(filename: str, content_type: str | None, file_size: int) -> str:
    """파일 유효성 검사. 확장자 반환"""
    ext = get_file_extension(filename)

    # MIME 타입으로도 체크
    if content_type and content_type in MIME_TO_EXT:
        mime_ext = MIME_TO_EXT[content_type]
        if ext != mime_ext:
            ext = mime_ext  # MIME 타입 우선

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(
            f"지원하지 않는 파일 형식입니다: .{ext}\n"
            f"지원 형식: PDF, DOCX, XLSX, HWP, HWPX"
        )

    if file_size > settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"파일 크기가 제한({settings.MAX_UPLOAD_SIZE_MB}MB)을 초과했습니다. "
            f"현재: {file_size / 1024 / 1024:.1f}MB"
        )

    if file_size == 0:
        raise ValueError("빈 파일은 업로드할 수 없습니다.")

    return ext


async def save_uploaded_file(file, user_id: str, db: AsyncSession) -> Document:
    """파일 저장 및 Document 레코드 생성"""
    # 파일 크기 사전 검증 (청크 단위 읽기로 메모리 보호)
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    chunks = []
    total_size = 0
    while True:
        chunk = await file.read(1024 * 1024)  # 1MB 단위
        if not chunk:
            break
        total_size += len(chunk)
        if total_size > max_size:
            raise ValueError(
                f"파일 크기가 제한({settings.MAX_UPLOAD_SIZE_MB}MB)을 초과했습니다."
            )
        chunks.append(chunk)
    content = b"".join(chunks)
    file_size = total_size

    # 유효성 검사
    ext = validate_file(file.filename, file.content_type, file_size)

    # 고유 파일명 생성
    file_id = str(uuid.uuid4())
    safe_filename = f"{file_id}.{ext}"
    filepath = os.path.join(settings.UPLOAD_DIR, safe_filename)

    # 디렉토리 확인
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # 파일 저장
    with open(filepath, "wb") as f:
        f.write(content)

    logger.info(f"파일 저장: {file.filename} ({file_size} bytes) → {safe_filename}")

    # DB 레코드 생성
    doc = Document(
        id=file_id,
        filename=file.filename,
        filepath=filepath,
        file_type=ext,
        file_size=file_size,
        status="uploading",
        uploaded_by=user_id,
    )
    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return doc


async def process_document_async(document_id: str):
    """비동기 문서 처리 (백그라운드 태스크)"""
    async with async_session() as db:
        try:
            # 문서 조회
            result = await db.execute(select(Document).where(Document.id == document_id))
            doc = result.scalar_one_or_none()
            if doc is None:
                logger.warning(f"문서를 찾을 수 없음: {document_id}")
                return

            # 상태 → processing
            doc.status = "processing"
            await db.commit()

            logger.info(f"문서 처리 시작: {doc.filename}")

            # 1. 텍스트 추출 (P3-8: PDF/DOCX는 비전 모델 우선 시도)
            # 동기 함수들은 run_in_executor로 실행하여 이벤트 루프 블로킹 방지
            loop = asyncio.get_running_loop()
            try:
                if doc.file_type == "pdf":
                    text = await loop.run_in_executor(
                        None, extract_pdf_with_vision, doc.filepath
                    )
                elif doc.file_type == "docx":
                    text = await loop.run_in_executor(
                        None, extract_docx_with_vision, doc.filepath
                    )
                else:
                    text = await loop.run_in_executor(
                        None, extract_text, doc.filepath, doc.file_type
                    )
            except Exception as e:
                doc.status = "failed"
                doc.error_message = f"텍스트 추출 실패: {str(e)[:200]}"
                await db.commit()
                logger.error(f"텍스트 추출 실패: {doc.filename} - {e}")
                return

            if not text or not text.strip():
                doc.status = "failed"
                doc.error_message = "텍스트를 추출할 수 없습니다. 파일이 비어있거나 이미지만 포함된 문서일 수 있습니다."
                await db.commit()
                logger.warning(f"빈 텍스트: {doc.filename}")
                return

            # 1-b. 페이지별 텍스트 (page_number 추적용)
            try:
                doc_pages = await loop.run_in_executor(
                    None, extract_pages, doc.filepath, doc.file_type
                )
            except Exception:
                doc_pages = []

            # 2. 시맨틱 청킹 (표 영역은 기존 방식 유지)
            chunks = await _semantic_chunk_document(
                text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP,
                generate_embeddings,
                split_into_paragraphs, semantic_chunk_with_embeddings, chunk_text,
                split_table_aware,
                doc.filename,
            )
            if not chunks:
                doc.status = "failed"
                doc.error_message = "텍스트 분할 결과가 없습니다."
                await db.commit()
                return

            logger.info(f"청킹 완료: {doc.filename} → {len(chunks)} chunks")

            # 3. 표 청크 자연어 변환 (임베딩용) — 원본은 content에 보존
            nl_texts = [table_chunk_to_nl(c) for c in chunks]

            # 4. 임베딩 생성 (자연어 변환본 사용)
            try:
                embeddings = await generate_embeddings(nl_texts)
            except Exception as e:
                doc.status = "failed"
                doc.error_message = f"임베딩 생성 실패: {str(e)[:200]}"
                await db.commit()
                logger.error(f"임베딩 실패: {doc.filename} - {e}")
                return

            # 5. DB 저장 (null 바이트 제거 - PostgreSQL UTF-8 거부 방지)
            for i, (chunk_content, nl_text, embedding) in enumerate(zip(chunks, nl_texts, embeddings)):
                clean_content = chunk_content.replace('\x00', '').replace('\uf000', '')
                clean_nl = nl_text.replace('\x00', '').replace('\uf000', '')
                nl_stored = clean_nl if clean_nl != clean_content else None
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=clean_content,
                    nl_content=nl_stored,
                    embedding=embedding,
                    page_number=_find_chunk_page(clean_content, doc_pages),
                    source_type=_detect_source_type(clean_content),
                )
                db.add(chunk)

            doc.status = "completed"
            doc.chunk_count = len(chunks)     # P3-6 Lineage: 청크 수 기록
            doc.updated_at = _utcnow()        # P3-6 Lineage: 처리 완료 시각
            await db.commit()
            logger.info(f"문서 처리 완료: {doc.filename} ({len(chunks)} chunks)")

        except Exception as e:
            logger.error(f"문서 처리 실패: {document_id} - {e}", exc_info=True)
            try:
                await db.rollback()
                result2 = await db.execute(select(Document).where(Document.id == document_id))
                doc2 = result2.scalar_one_or_none()
                if doc2:
                    doc2.status = "failed"
                    doc2.error_message = f"처리 중 오류: {str(e)[:300]}"
                    await db.commit()
            except Exception:
                logger.error("상태 업데이트 실패")


async def delete_document(document_id: str, db: AsyncSession) -> bool:
    """문서 및 청크 삭제"""
    result = await db.execute(select(Document).where(Document.id == document_id))
    doc = result.scalar_one_or_none()
    if doc is None:
        return False

    # 파일 삭제
    try:
        if os.path.exists(doc.filepath):
            os.remove(doc.filepath)
    except OSError as e:
        logger.warning(f"파일 삭제 실패: {doc.filepath} - {e}")

    # DB 삭제 (cascade로 chunks도 삭제)
    await db.delete(doc)
    await db.commit()
    logger.info(f"문서 삭제: {doc.filename}")
    return True


async def _semantic_chunk_document(
    text: str,
    chunk_size: int,
    chunk_overlap: int,
    generate_embeddings_fn,
    split_into_paragraphs_fn,
    semantic_chunk_fn,
    fallback_chunk_fn,
    split_table_aware_fn,
    filename: str = "",
) -> List[str]:
    """시맨틱 청킹 메인 로직.
    - 표 영역: 기존 헤더반복 방식 유지
    - 일반 텍스트: 단락 임베딩 유사도 기반 시맨틱 경계 탐지
    - 실패 시 자동 폴백 (문자 기반 슬라이딩 윈도우)
    """
    segments = split_table_aware_fn(text.strip())
    chunks: List[str] = []

    for seg_type, seg_lines, header in segments:
        seg_text = "\n".join(seg_lines).strip()
        if not seg_text:
            continue

        if seg_type == "table":
            # 표: 기존 헤더반복 방식
            table_chunks = fallback_chunk_fn(seg_text, chunk_size, chunk_overlap)
            chunks.extend(table_chunks)
            continue

        # 일반 텍스트: 시맨틱 청킹
        paragraphs = split_into_paragraphs_fn(seg_text)

        if len(paragraphs) < 2:
            # 단락이 1개면 폴백
            chunks.extend(fallback_chunk_fn(seg_text, chunk_size, chunk_overlap))
            continue

        try:
            para_embeddings = await generate_embeddings_fn(paragraphs)
            semantic_chunks = semantic_chunk_fn(
                paragraphs,
                para_embeddings,
                similarity_threshold=settings.SEMANTIC_SIMILARITY_THRESHOLD,
                max_chunk_size=chunk_size,
            )
            # 시맨틱 청킹 결과가 너무 크면 폴백으로 추가 분할
            final = []
            for sc in semantic_chunks:
                if len(sc) > chunk_size * 1.5:
                    final.extend(fallback_chunk_fn(sc, chunk_size, chunk_overlap))
                else:
                    final.append(sc)
            chunks.extend(final)
            logger.debug(f"[시맨틱청킹] {filename}: {len(paragraphs)}단락 → {len(final)}청크")
        except Exception as e:
            logger.warning(f"시맨틱 청킹 실패 ({filename}), 폴백: {e}")
            chunks.extend(fallback_chunk_fn(seg_text, chunk_size, chunk_overlap))

    return [c for c in chunks if c and c.strip()]
