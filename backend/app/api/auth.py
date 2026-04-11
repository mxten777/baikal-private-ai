"""
Auth API - 로그인, 토큰 갱신
P3-4: JWT HttpOnly 쿠키 전환 (localStorage → HttpOnly Cookie, XSS 방어)
P3-5: Refresh 토큰 블랙리스트 (Token Rotation)
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.config import get_settings
from app.schemas.user import (
    LoginRequest, TokenRefreshRequest,
    UserResponse, PasswordChangeRequest, PasswordChangeResponse,
)
from app.services.auth_service import (
    authenticate_user, create_tokens,
    blacklist_refresh_token, is_token_blacklisted,
)
from app.core.security import decode_token, verify_password, hash_password
from app.core.deps import get_current_user
from app.core.limits import limiter
from app.models.user import User
from sqlalchemy import select

router = APIRouter(prefix="/api/auth", tags=["auth"])
settings = get_settings()


def _set_auth_cookies(response: Response, tokens: dict) -> None:
    """HttpOnly 쿠키로 토큰 설정 (P3-4)"""
    access_max_age = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    refresh_max_age = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
    # HTTPS 환경에서는 secure=True 로 변경 필요
    response.set_cookie(
        "access_token", tokens["access_token"],
        httponly=True, max_age=access_max_age,
        samesite="lax", secure=False, path="/",
    )
    response.set_cookie(
        "refresh_token", tokens["refresh_token"],
        httponly=True, max_age=refresh_max_age,
        samesite="lax", secure=False, path="/api/auth",
    )


def _clear_auth_cookies(response: Response) -> None:
    """쿠키 삭제"""
    response.delete_cookie("access_token", path="/")
    response.delete_cookie("refresh_token", path="/api/auth")


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """로그인 — HttpOnly 쿠키로 토큰 발급 (분당 5회 제한)"""
    user = await authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
        )
    tokens = create_tokens(user)
    _set_auth_cookies(response, tokens)
    return {"token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    body: TokenRefreshRequest | None = None,
):
    """토큰 갱신 — 쿠키 우선, body 폴백 (P3-4 + P3-5 Token Rotation)"""
    # 쿠키 우선, body 폴백 (Swagger UI 호환)
    raw_token = request.cookies.get("refresh_token")
    if not raw_token and body:
        raw_token = body.refresh_token
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="리프레시 토큰이 없습니다",
        )

    payload = decode_token(raw_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다",
        )

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(db, jti):
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이미 폐기된 토큰입니다",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        _clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
        )

    # 구 토큰 블랙리스트 등록 (Token Rotation)
    if jti:
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
        if expires_at:
            await blacklist_refresh_token(db, jti=jti, user_id=user_id, expires_at=expires_at)

    tokens = create_tokens(user)
    _set_auth_cookies(response, tokens)
    return {"token_type": "bearer"}


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    body: TokenRefreshRequest | None = None,
):
    """로그아웃 — Refresh 토큰 폐기 + 쿠키 삭제 (P3-4 + P3-5)"""
    raw_token = request.cookies.get("refresh_token")
    if not raw_token and body:
        raw_token = body.refresh_token

    if raw_token:
        payload = decode_token(raw_token)
        if payload and payload.get("type") == "refresh":
            jti = payload.get("jti")
            user_id = payload.get("sub")
            exp = payload.get("exp")
            if jti and user_id and exp:
                expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
                await blacklist_refresh_token(db, jti=jti, user_id=user_id, expires_at=expires_at)

    _clear_auth_cookies(response)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보"""
    return current_user


@router.patch("/password", response_model=PasswordChangeResponse)
async def change_password(
    request: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """비밀번호 변경"""
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다",
        )

    current_user.password_hash = hash_password(request.new_password)
    await db.commit()

    return {"message": "비밀번호가 성공직으로 변경되었습니다"}



@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(request: Request, body: LoginRequest, db: AsyncSession = Depends(get_db)):
    """로그인 (분당 5회 시도 제한)"""
    user = await authenticate_user(db, body.username, body.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다",
        )
    tokens = create_tokens(user)
    return tokens


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """토큰 갱신 (P3-5: 구 Refresh 토큰 블랙리스트 등록 후 신규 발급)"""
    payload = decode_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다",
        )

    jti = payload.get("jti")
    if jti and await is_token_blacklisted(db, jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이미 폐기된 토큰입니다",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다",
        )

    # 구 토큰 블랙리스트 등록 (Token Rotation)
    if jti:
        exp = payload.get("exp")
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc) if exp else None
        if expires_at:
            await blacklist_refresh_token(db, jti=jti, user_id=user_id, expires_at=expires_at)

    tokens = create_tokens(user)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """로그아웃 — Refresh 토큰 즉시 폐기 (P3-5)"""
    payload = decode_token(request.refresh_token)
    if payload is None or payload.get("type") != "refresh":
        # 이미 만료됐거나 잘못된 토큰도 로그아웃 성공으로 처리
        return

    jti = payload.get("jti")
    user_id = payload.get("sub")
    exp = payload.get("exp")
    if jti and user_id and exp:
        expires_at = datetime.fromtimestamp(exp, tz=timezone.utc)
        await blacklist_refresh_token(db, jti=jti, user_id=user_id, expires_at=expires_at)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보"""
    return current_user


@router.patch("/password", response_model=PasswordChangeResponse)
async def change_password(
    request: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """비밀번호 변경"""
    # 현재 비밀번호 확인
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다",
        )

    # 비밀번호 업데이트 (길이 검사는 PasswordChangeRequest 스키마에서 처리됨)
    current_user.password_hash = hash_password(request.new_password)
    await db.commit()

    return {"message": "비밀번호가 성공적으로 변경되었습니다"}
