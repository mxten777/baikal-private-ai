"""
BAIKAL Private AI - Configuration
"""
from pydantic_settings import BaseSettings
from pydantic import model_validator
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://baikal:baikal_secret_2024@postgres:5432/baikal_ai"

    # JWT
    SECRET_KEY: str = "change-this-to-random-secret-key-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # Ollama
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    LLM_MODEL: str = "qwen2.5:7b"
    EMBEDDING_MODEL: str = "bge-m3"

    # App
    APP_ENV: str = "production"
    DEFAULT_ADMIN_USERNAME: str = "admin"
    DEFAULT_ADMIN_PASSWORD: str = "admin1234"

    # Upload
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE_MB: int = 100

    # RAG
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.50
    EMBEDDING_DIMENSION: int = 1024
    MIN_HYBRID_SCORE: float = 0.45
    SEMANTIC_SIMILARITY_THRESHOLD: float = 0.75
    CROSS_ENCODER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    MAX_HISTORY_TURNS: int = 3

    # LLM Options
    LLM_NUM_CTX: int = 8192
    LLM_NUM_PREDICT: int = 1024
    LLM_TEMPERATURE: float = 0.3

    # OCR
    OCR_MIN_TEXT_PER_PAGE: int = 30
    OCR_DPI: int = 200

    # CORS — 개발 시 http://localhost:3000 추가; 운영 시 실제 도메인으로 변경
    CORS_ORIGINS: list = [
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
    ]

    @model_validator(mode="after")
    def validate_production_secrets(self) -> "Settings":
        if self.APP_ENV == "production":
            if self.SECRET_KEY == "change-this-to-random-secret-key-in-production":
                raise ValueError(
                    "SECRET_KEY가 기본값입니다. "
                    ".env 파일에서 안전한 랜덤 키로 변경하세요. "
                    "(예: python -c \"import secrets; print(secrets.token_hex(32))\")"
                )
            if len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "SECRET_KEY는 최소 32자 이상이어야 합니다."
                )
            if self.DEFAULT_ADMIN_PASSWORD in ("admin1234", "admin", "password", "1234"):
                raise ValueError(
                    "DEFAULT_ADMIN_PASSWORD가 취약한 기본값입니다. "
                    ".env 파일에서 강력한 비밀번호로 변경하세요."
                )
        return self

    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
