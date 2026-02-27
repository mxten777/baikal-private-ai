"""
BAIKAL Private AI - Database Configuration
"""
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

settings = get_settings()
logger = logging.getLogger("baikal.db")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,  # 연결 유효성 사전 체크
    pool_recycle=3600,    # 1시간마다 연결 재활용
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """DB 초기화: 테이블 생성 + pgvector 확장 + 인덱스"""
    from sqlalchemy import text
    async with engine.begin() as conn:
        # pgvector 확장
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("pgvector 확장 활성화")

        # 테이블 생성
        await conn.run_sync(Base.metadata.create_all)
        logger.info("테이블 생성 완료")

        # Vector 검색 인덱스 (HNSW - 데이터 없이도 생성 가능, 높은 정확도)
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chunk_embedding 
            ON document_chunks 
            USING hnsw (embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64)
        """))

        # 추가 인덱스
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_status 
            ON documents (status)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by 
            ON documents (uploaded_by)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_sessions_user 
            ON chat_sessions (user_id)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_chat_messages_session 
            ON chat_messages (session_id)
        """))

        logger.info("인덱스 생성 완료")
