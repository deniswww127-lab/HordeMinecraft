"""Подключение к БД и выдача async-сессий."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .config import settings
from .models import Base

engine = create_async_engine(settings.DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def init_db():
    """Создаёт таблицы при старте (для прода используйте Alembic-миграции)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncSession:
    async with SessionLocal() as session:
        yield session
