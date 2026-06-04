"""
Конфигурация ПостПилот.
Все секреты берутся из переменных окружения (.env), в коде не хранятся.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- VK OAuth (приложение с dev.vk.com) ---
    VK_CLIENT_ID: str = "4huV53h3Yccv0iC3oZPf"
    VK_CLIENT_SECRET: str = "6b47fab66b47fab66b47fab6c16806873966b476b47fab601668ce83cc8d186a44c7c1e"
    VK_REDIRECT_URI: str = "https://postpilotvk.onrender.com/auth/vk/callback"
    VK_API_VERSION: str = "5.199"

    # --- LLM для генерации текста ---
    ANTHROPIC_API_KEY: str = ""
    LLM_MODEL: str = "claude-sonnet-4-20250514"

    # --- Инфраструктура ---
    DATABASE_URL: str = "sqlite+aiosqlite:///./postpilot.db"
    SECRET_KEY: str = "change-me-in-production"          # для подписи сессий
    BASE_URL: str = "https://your-domain.ru"

    # --- Лимиты VK (анти-бан) ---
    POST_RATE_LIMIT_SECONDS: int = 30   # минимальный интервал между постами в одну группу


settings = Settings()
