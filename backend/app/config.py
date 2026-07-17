from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repo root: config.py -> app -> backend -> RhFlow
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    APP_NAME: str
    DEBUG: bool
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    LLM_PROVIDER: str
    LLM_API_KEY: str
    LLM_BASE_URL: str
    LLM_MODEL: str
    LLAMA_CLOUD_API_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    MINIO_ENDPOINT: str
    MINIO_PUBLIC_ENDPOINT: str
    MINIO_PUBLIC_SECURE: bool = False
    MINIO_PUBLIC_PATH_PREFIX: str = ""
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_BUCKET: str
    MINIO_CANDIDATURES_BUCKET: str | None = None
    MINIO_SECURE: bool = False
    LITEPARSE_QUIET: bool = True
    LITEPARSE_MAX_PAGES: int | None = 10
    LITEPARSE_OCR_ENABLED: bool = True
    LITEPARSE_OCR_LANGUAGE: str | None = "fra+eng"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
