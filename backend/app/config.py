"""Application configuration using Pydantic BaseSettings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://wearable:wearable@db:5432/wearable"

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"

    # Open Wearables
    OW_API_URL: str = "http://ow-backend:8000"
    OW_API_KEY: str = ""

    # JWT
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # Sync
    SYNC_INTERVAL_MINUTES: int = 60

    # Ollama (LLM)
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "mistral-nemo:latest"
    LLM_CACHE_TTL_SECONDS: int = 3600

    # App
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()
