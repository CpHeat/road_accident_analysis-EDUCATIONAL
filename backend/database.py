import os

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://test_user:example@localhost:5432/accidents"
)


engine = create_async_engine(DATABASE_URL, echo=False)

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency pour obtenir une session de base de données."""
    async with async_session() as session:
        yield session


async def init_db():
    """Crée les tables si elles n'existent pas."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
