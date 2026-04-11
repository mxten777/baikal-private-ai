"""
BAIKAL Private AI - Main Application
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.config import get_settings
from app.database import init_db, async_session
from app.api import auth, users, documents, chat, search, admin
from app.services.auth_service import create_default_admin
from app.core.limits import limiter

settings = get_settings()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("baikal")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 시작/종료 이벤트"""
    logger.info("시스템 초기화 중...")

    # DB 초기화 (재시도 로직)
    for attempt in range(5):
        try:
            await init_db()
            logger.info("DB 초기화 완료")
            break
        except Exception as e:
            logger.warning(f"DB 연결 실패 (시도 {attempt + 1}/5): {e}")
            if attempt < 4:
                await asyncio.sleep(3)
            else:
                logger.error("DB 연결 실패 - 서버 시작 불가")
                raise

    # 기본 관리자 생성
    async with async_session() as db:
        await create_default_admin(
            db,
            settings.DEFAULT_ADMIN_USERNAME,
            settings.DEFAULT_ADMIN_PASSWORD,
        )

    # 고착 문서 복구 — 서버 재시작 전 처리 중이던 문서를 failed로 표시
    async with async_session() as db:
        from sqlalchemy import update
        from app.models.document import Document
        result = await db.execute(
            update(Document)
            .where(Document.status.in_(["processing", "uploading"]))
            .values(
                status="failed",
                error_message="서버 재시작으로 인해 처리가 중단되었습니다. 파일을 다시 업로드해주세요.",
            )
            .returning(Document.id)
        )
        recovered = result.fetchall()
        if recovered:
            logger.warning(f"고착 문서 {len(recovered)}건을 failed 상태로 복구했습니다: {[r[0] for r in recovered]}")
        await db.commit()

    logger.info("시스템 준비 완료")
    yield
    logger.info("시스템 종료")


app = FastAPI(
    title="BAIKAL Private AI",
    description="폐쇄망 설치형 문서검색·답변 AI 플랫폼",
    version="1.0.0",
    lifespan=lifespan,
)

# Rate limiter 등록
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 글로벌 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"처리되지 않은 예외: {request.method} {request.url} - {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "서버 내부 오류가 발생했습니다. 잠시 후 다시 시도해주세요."},
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )

# CORS — P3-4: credentials=True (HttpOnly 쿠키 지원), 지정 origin 필수
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type"],
)

# 라우터 등록
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(search.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health_check():
    """헬스체크 - 서비스 상태 확인"""
    from app.services.llm_service import check_ollama_health
    from app.database import engine
    from sqlalchemy import text

    # DB 상태
    db_ok = False
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass

    # Ollama 상태
    ollama_ok = await check_ollama_health()

    status = "ok" if (db_ok and ollama_ok) else "degraded"
    if not db_ok:
        status = "error"

    return {
        "status": status,
        "service": "BAIKAL Private AI",
        "version": "1.0.0",
        "components": {
            "database": "connected" if db_ok else "disconnected",
            "ollama": "connected" if ollama_ok else "disconnected",
        },
    }
