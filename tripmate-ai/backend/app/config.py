"""
TripMate AI - Application Configuration
Uses Pydantic Settings v2 for validated, type-safe environment configuration.
"""

from typing import List, Literal, Optional
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Core Application Settings
    APP_NAME: str = Field(default="TripMate AI")
    APP_VERSION: str = Field(default="1.0.0")
    APP_ENV: Literal["development", "staging", "production", "testing"] = Field(
        default="development"
    )
    DEBUG: bool = Field(default=True)
    API_V1_PREFIX: str = Field(default="/api/v1")

    # Server Settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Security Settings
    SECRET_KEY: str = Field(
        default="development-insecure-secret-key-change-in-production-min32chars"
    )
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=60)
    REQUIRE_API_KEY: bool = Field(default=False)
    MASTER_API_KEY: Optional[str] = Field(default=None)

    # CORS Settings
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"]
    )

    # Logging Settings
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO"
    )
    LOG_FORMAT: Literal["json", "text"] = Field(default="json")

    # LLM Settings
    LLM_PROVIDER: Literal["openai", "ollama", "mock"] = Field(default="mock")
    OPENAI_API_KEY: Optional[str] = Field(default=None)
    OPENAI_MODEL: str = Field(default="gpt-4o")
    OLLAMA_BASE_URL: str = Field(default="http://localhost:11434")
    OLLAMA_MODEL: str = Field(default="llama3.1")
    LLM_TIMEOUT: int = Field(default=60)
    LLM_MAX_RETRIES: int = Field(default=3)

    # Database Settings
    POSTGRES_SERVER: str = Field(default="localhost")
    POSTGRES_PORT: int = Field(default=5432)
    POSTGRES_USER: str = Field(default="tripmate")
    POSTGRES_PASSWORD: str = Field(default="tripmate_password")
    POSTGRES_DB: str = Field(default="tripmate_db")
    DATABASE_URL: Optional[str] = Field(default=None)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # RAG Settings
    VECTOR_STORE_TYPE: Literal["pgvector", "memory"] = Field(default="memory")
    EMBEDDING_PROVIDER: Literal["openai", "mock"] = Field(default="mock")

    # Agent Orchestration Settings
    MAX_RETRY_COUNT: int = Field(default=3)
    APPROVAL_TIMEOUT_HOURS: int = Field(default=24)


# Global settings singleton
settings = Settings()

