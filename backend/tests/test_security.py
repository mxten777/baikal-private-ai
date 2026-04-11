"""
P3-7: security.py 유닛 테스트 — JWT 토큰 생성/검증, 비밀번호 해싱
"""
import time
import pytest
from datetime import timedelta

# conftest가 env를 먼저 설정
from tests.conftest import *  # noqa: F401, F403
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        hashed = hash_password("mypassword123")
        assert hashed != "mypassword123"

    def test_verify_correct_password(self):
        hashed = hash_password("mypassword123")
        assert verify_password("mypassword123", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("mypassword123")
        assert verify_password("wrongpassword", hashed) is False

    def test_different_hashes_same_password(self):
        """bcrypt는 salt가 달라 같은 입력도 해시가 다름"""
        h1 = hash_password("samepassword")
        h2 = hash_password("samepassword")
        assert h1 != h2
        assert verify_password("samepassword", h1)
        assert verify_password("samepassword", h2)


class TestAccessToken:
    def test_create_and_decode(self):
        data = {"sub": "user-123", "username": "testuser", "role": "user"}
        token = create_access_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"

    def test_expired_token_returns_none(self):
        data = {"sub": "user-123", "username": "testuser", "role": "user"}
        token = create_access_token(data, expires_delta=timedelta(seconds=-1))
        payload = decode_token(token)
        assert payload is None

    def test_tampered_token_returns_none(self):
        data = {"sub": "user-123", "username": "testuser", "role": "user"}
        token = create_access_token(data)
        tampered = token[:-5] + "XXXXX"
        assert decode_token(tampered) is None

    def test_invalid_string_returns_none(self):
        assert decode_token("not.a.jwt") is None
        assert decode_token("") is None


class TestRefreshToken:
    def test_create_and_decode(self):
        data = {"sub": "user-123", "username": "testuser", "role": "user"}
        token, jti = create_refresh_token(data)
        payload = decode_token(token)
        assert payload is not None
        assert payload["type"] == "refresh"
        assert payload["jti"] == jti

    def test_jti_is_unique(self):
        data = {"sub": "user-123", "username": "testuser", "role": "user"}
        _, jti1 = create_refresh_token(data)
        _, jti2 = create_refresh_token(data)
        assert jti1 != jti2

    def test_access_token_rejected_as_refresh(self):
        data = {"sub": "user-123", "username": "testuser", "role": "user"}
        access_token = create_access_token(data)
        payload = decode_token(access_token)
        assert payload["type"] != "refresh"
