"""
TripMate AI - Database Session & Connection Management
Configures SQLAlchemy 2.0 async engine, sessionmaker, SQLite fallback, and table initialization.
"""

from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.database.base import Base
import app.database.models  # noqa: F401 - ensure models are registered on Base.metadata
from app.utils.logger import get_logger

logger = get_logger(__name__)


def is_postgres_server_available(host: str, port: int) -> bool:
    """Checks if the PostgreSQL server port is actively accepting connections."""
    import socket
    try:
        with socket.create_connection((host, port), timeout=0.3):
            return True
    except (socket.error, OSError):
        return False


def get_database_url() -> str:
    """
    Returns database connection URL, ensuring async driver prefix.
    If PostgreSQL is unreachable in local environment, cleanly falls back
    to a persistent SQLite database (aiosqlite).
    """
    if settings.DATABASE_URL:
        raw_url = settings.DATABASE_URL
    else:
        # Check if configured Postgres server is reachable
        if is_postgres_server_available(settings.POSTGRES_SERVER, settings.POSTGRES_PORT):
            raw_url = settings.SQLALCHEMY_DATABASE_URI
        else:
            logger.info(
                "PostgreSQL server (%s:%s) is not reachable; falling back to local 'sqlite+aiosqlite:///tripmate.db'",
                settings.POSTGRES_SERVER,
                settings.POSTGRES_PORT,
            )
            raw_url = "sqlite+aiosqlite:///tripmate.db"

    if raw_url.startswith("postgresql://"):
        return raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return raw_url


# Determine primary engine
_database_url = get_database_url()
logger.info("Initializing async database engine with URL: %s", _database_url.split("@")[-1] if "@" in _database_url else _database_url)

try:
    async_engine: AsyncEngine = create_async_engine(
        _database_url,
        echo=False,
        future=True,
    )
except Exception as exc:
    logger.warning("Failed creating primary async engine (%s), falling back to aiosqlite", exc)
    _database_url = "sqlite+aiosqlite:///tripmate.db"
    async_engine = create_async_engine(_database_url, echo=False)

# When running on SQLite fallback, ensure all tables are immediately ready
if "sqlite" in _database_url:
    try:
        from sqlalchemy import create_engine
        sync_url = _database_url.replace("+aiosqlite", "")
        sync_engine = create_engine(sync_url)
        Base.metadata.create_all(sync_engine)
        logger.info("Auto-initialized local SQLite tables in '%s'", sync_url)
    except Exception as exc:
        logger.warning("Could not auto-create SQLite tables: %s", exc)

async_session_maker = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an async database session per request."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db(engine: Optional[AsyncEngine] = None) -> None:
    """Initializes declarative database schema tables."""
    eng = engine or async_engine
    logger.info("Initializing database schema via Base.metadata.create_all...")
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema initialized successfully.")
