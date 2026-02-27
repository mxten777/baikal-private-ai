"""
BAIKAL Private AI - Configuration
"""
from pydantic_settings import BaseSettings
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
    LLM_MODEL: str = "llama3"
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
    EMBEDDING_DIMENSION: int = 1024

    class Config:
        env_file = "../.env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
