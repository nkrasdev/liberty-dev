import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from shared.utils.logging import get_logger

logger = get_logger(__name__)

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/aggregator")

# Create async engine
engine = create_async_engine(
    DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database connection."""
    try:
        # Test connection
        async with engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: sync_conn.execute("SELECT 1"))
        logger.info("Database connection established")
    except Exception as e:
        logger.error("Failed to connect to database", error=str(e))
        raise
