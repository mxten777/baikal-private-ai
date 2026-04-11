"""
P3-7: auth_service.py 유닛 테스트 — DB를 AsyncMock으로 대체
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from tests.conftest import *  # noqa: F401, F403
from app.services.auth_service import (
    authenticate_user,
    create_tokens,
    blacklist_refresh_token,
    is_token_blacklisted,
)
from app.core.security import hash_password, decode_token
from app.models.user import User


def _make_user(username="testuser", password="P@ssword1", role="user", is_active=True):
    """테스트용 User 객체 생성"""
    user = MagicMock(spec=User)
    user.id = "user-uuid-001"
    user.username = username
    user.password_hash = hash_password(password)
    user.role = role
    user.is_active = is_active
    return user


class TestAuthenticateUser:
    @pytest.mark.asyncio
    async def test_correct_credentials(self):
        user = _make_user()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=mock_result)

        result = await authenticate_user(db, "testuser", "P@ssword1")
        assert result is user

    @pytest.mark.asyncio
    async def test_wrong_password(self):
        user = _make_user()
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=mock_result)

        result = await authenticate_user(db, "testuser", "wrongpassword")
        assert result is None

    @pytest.mark.asyncio
    async def test_user_not_found(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        result = await authenticate_user(db, "nonexistent", "anypassword")
        assert result is None

    @pytest.mark.asyncio
    async def test_inactive_user_rejected(self):
        user = _make_user(is_active=False)
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=mock_result)

        result = await authenticate_user(db, "testuser", "P@ssword1")
        assert result is None


class TestCreateTokens:
    def test_returns_access_and_refresh(self):
        user = _make_user()
        tokens = create_tokens(user)
        assert "access_token" in tokens
        assert "refresh_token" in tokens
        assert tokens["token_type"] == "bearer"

    def test_access_token_payload(self):
        user = _make_user()
        tokens = create_tokens(user)
        payload = decode_token(tokens["access_token"])
        assert payload["sub"] == user.id
        assert payload["type"] == "access"

    def test_refresh_token_payload(self):
        user = _make_user()
        tokens = create_tokens(user)
        payload = decode_token(tokens["refresh_token"])
        assert payload["sub"] == user.id
        assert payload["type"] == "refresh"
        assert "jti" in payload

    def test_jti_matches_refresh_jti(self):
        user = _make_user()
        tokens = create_tokens(user)
        payload = decode_token(tokens["refresh_token"])
        assert payload["jti"] == tokens["refresh_jti"]


class TestTokenBlacklist:
    @pytest.mark.asyncio
    async def test_blacklist_and_check(self):
        db = AsyncMock()
        db.execute = AsyncMock()
        db.commit = AsyncMock()
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)

        await blacklist_refresh_token(db, jti="test-jti-001", user_id="user-001", expires_at=expires_at)
        db.execute.assert_called_once()
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_is_blacklisted_true(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = (1,)  # 존재
        db.execute = AsyncMock(return_value=mock_result)

        result = await is_token_blacklisted(db, "blacklisted-jti")
        assert result is True

    @pytest.mark.asyncio
    async def test_is_blacklisted_false(self):
        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None  # 없음
        db.execute = AsyncMock(return_value=mock_result)

        result = await is_token_blacklisted(db, "clean-jti")
        assert result is False
