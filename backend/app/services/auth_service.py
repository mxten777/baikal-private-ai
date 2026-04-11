"""
Auth Service
"""
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, text
from app.models.user import User
from app.core.security import verify_password, hash_password, create_access_token, create_refresh_token


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User | None:
    """사용자 인증"""
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None or not verify_password(password, user.password_hash):
        return None
    if not user.is_active:
        return None
    return user


def create_tokens(user: User) -> dict:
    """JWT 토큰 생성"""
    token_data = {"sub": user.id, "username": user.username, "role": user.role}
    access_token = create_access_token(token_data)
    refresh_token, jti = create_refresh_token(token_data)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_jti": jti,  # 내부 전달용 (응답에 포함되지 않음)
        "token_type": "bearer",
    }


async def blacklist_refresh_token(db: AsyncSession, jti: str, user_id: str, expires_at: datetime):
    """Refresh 토큰 JTI를 블랙리스트에 등록 (P3-5)."""
    await db.execute(
        text(
            "INSERT INTO refresh_token_blacklist (jti, user_id, expires_at) "
            "VALUES (:jti, :user_id, :expires_at) "
            "ON CONFLICT (jti) DO NOTHING"
        ),
        {"jti": jti, "user_id": user_id, "expires_at": expires_at},
    )
    await db.commit()


async def is_token_blacklisted(db: AsyncSession, jti: str) -> bool:
    """JTI가 블랙리스트에 있으면 True."""
    result = await db.execute(
        text("SELECT 1 FROM refresh_token_blacklist WHERE jti = :jti"),
        {"jti": jti},
    )
    return result.fetchone() is not None


async def cleanup_expired_blacklist(db: AsyncSession):
    """만료된 블랙리스트 항목 정리 (선택적 호출)."""
    await db.execute(
        text("DELETE FROM refresh_token_blacklist WHERE expires_at < NOW()")
    )
    await db.commit()


async def create_default_admin(db: AsyncSession, username: str, password: str):
    """기본 관리자 계정 생성 (없으면)"""
    result = await db.execute(select(User).where(User.username == username))
    existing = result.scalar_one_or_none()
    if existing is None:
        admin = User(
            username=username,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        print(f"[INIT] 기본 관리자 계정 생성: {username}")
    else:
        print(f"[INIT] 관리자 계정 이미 존재: {username}")
