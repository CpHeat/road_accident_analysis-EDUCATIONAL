import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "accidents")

if not POSTGRES_USER or not POSTGRES_PASSWORD:
    raise ValueError("DATABASE_URL or POSTGRES_USER and POSTGRES_PASSWORD must be set")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"


engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator:
    """Dependency pour obtenir une session de base de données."""
    async with async_session() as session:
        yield session


async def init_db() -> None:
    """Crée les tables si elles n'existent pas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
