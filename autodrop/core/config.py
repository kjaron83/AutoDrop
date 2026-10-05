"""Application settings and configuration management."""

from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General
    APP_NAME: str = "AutoDrop"
    APP_EMAIL: str | None = None
    ENVIRONMENT: Literal["development", "production", "test"] = "development"
    APP_DOMAIN: str = "http://localhost:8000"
    SECRET_KEY: str = "insecure-secret-key-for-development-only-min-32-chars-long"

    # Database
    DATABASE_URL: str = "sqlite:///./autodrop.db"

    # Internationalization (i18n)
    DEFAULT_LOCALE: str = "hu"
    SUPPORTED_LOCALES: list[str] = ["hu", "en"]

    # Authentication & Session
    SESSION_COOKIE_NAME: str = "autodrop_session"
    SESSION_MAX_AGE_SECONDS: int = 60 * 60 * 24 * 7  # 7 days
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 2

    # SMTP Settings
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str = "noreply@autodrop.local"
    SMTP_TLS: bool = True

    # Logging Settings
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FORMAT: Literal["text", "json"] = "text"
    LOG_FILE: str | None = None
    LOG_MAX_BYTES: int = 10_485_760  # 10 MB
    LOG_BACKUP_COUNT: int = 5

    @property
    def is_dev(self) -> bool:
        """Returns True if the current environment is development."""
        return self.ENVIRONMENT == "development"

    @property
    def is_test(self) -> bool:
        """Returns True if the current environment is test."""
        return self.ENVIRONMENT == "test"

    @property
    def is_prod(self) -> bool:
        """Returns True if the current environment is production."""
        return self.ENVIRONMENT == "production"


settings = Settings()
