from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_NAME: str = "SpiritualSakha"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database & Redis
    DATABASE_URL: str = "postgresql+asyncpg://sakha:sakha_dev_password@localhost:5432/spiritualsakha"
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT & Security
    JWT_SECRET: str = "spiritualsakha_dev_secret_key_change_in_production_32chars"
    JWT_ACCESS_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"

    # Gemini AI
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-1.5-pro"

    # Astrology & System
    DEFAULT_TIMEZONE: str = "Asia/Kolkata"
    ASTROLOGY_AYANAMSA: str = "LAHIRI"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


@lru_cache()
def get_settings() -> Settings:
    return Settings()
