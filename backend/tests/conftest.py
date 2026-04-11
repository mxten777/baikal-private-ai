"""
pytest conftest — 공통 픽스처
"""
import os
import pytest

# 테스트 환경에서는 production 검증 우회
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32chars-minimum-padding")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://baikal:baikal_secret_2024@localhost:5432/baikal_ai",
)
