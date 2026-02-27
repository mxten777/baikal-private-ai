"""
Auth Service
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    return {
        "access_token": create_access_token(token_data),
        "refresh_token": create_refresh_token(token_data),
        "token_type": "bearer",
    }


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
