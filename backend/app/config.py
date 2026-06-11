from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


# Repo root: config.py -> app -> backend -> RhFlow
ENV_FILE = Path(__file__).resolve().parents[2] / ".env"


class Settings(BaseSettings):
    APP_NAME: str = "RH Flow v2"
    DEBUG: bool = False
    DATABASE_URL: str  # mandatory — no default, app fails fast if missing
    SECRET_KEY: str    # mandatory — no default
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    MINIO_ENDPOINT: str = "localhost:9000"  # compose overrides with minio:9000

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
