"""
Document Service - 파일 업로드, 관리, 비동기 처리
"""
import os
import uuid
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.document import Document, DocumentChunk
from app.config import get_settings
from app.database import async_session

settings = get_settings()
logger = logging.getLogger("baikal.document")

ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx"}
MIME_TO_EXT = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
}


def get_file_extension(filename: str) -> str:
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


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
            f"지원 형식: PDF, DOCX, XLSX"
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
    from app.rag.loader import extract_text
    from app.rag.chunker import chunk_text
    from app.rag.embedder import generate_embeddings

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

            # 1. 텍스트 추출
            try:
                text = extract_text(doc.filepath, doc.file_type)
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

            # 2. 텍스트 청킹
            chunks = chunk_text(text, settings.CHUNK_SIZE, settings.CHUNK_OVERLAP)
            if not chunks:
                doc.status = "failed"
                doc.error_message = "텍스트 분할 결과가 없습니다."
                await db.commit()
                return

            logger.info(f"청킹 완료: {doc.filename} → {len(chunks)} chunks")

            # 3. 임베딩 생성
            try:
                embeddings = await generate_embeddings(chunks)
            except Exception as e:
                doc.status = "failed"
                doc.error_message = f"임베딩 생성 실패: {str(e)[:200]}"
                await db.commit()
                logger.error(f"임베딩 실패: {doc.filename} - {e}")
                return

            # 4. DB 저장
            for i, (chunk_content, embedding) in enumerate(zip(chunks, embeddings)):
                chunk = DocumentChunk(
                    document_id=document_id,
                    chunk_index=i,
                    content=chunk_content,
                    embedding=embedding,
                )
                db.add(chunk)

            doc.status = "completed"
            await db.commit()
            logger.info(f"문서 처리 완료: {doc.filename} ({len(chunks)} chunks)")

        except Exception as e:
            logger.error(f"문서 처리 실패: {document_id} - {e}", exc_info=True)
            try:
                doc.status = "failed"
                doc.error_message = f"처리 중 오류: {str(e)[:300]}"
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
