from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

# Engine = the connection pool to PostgreSQL
# - pool_size=5: keep 5 connections open and ready
# - echo=True: print every SQL query to console (great for learning, disable in prod)
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=5,
    echo=True,
)

# Session factory = creates new sessions from the pool
# - expire_on_commit=False: after commit, objects stay usable
#   (without this, accessing user.email after commit would hit DB again)
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --- Sync engine (for Celery workers) ---
# Celery workers are sync processes — no event loop, no async.
# So we need a plain sync connection for DB access inside tasks.
# Convert: postgresql+asyncpg://... → postgresql+psycopg2://...
SYNC_DATABASE_URL = settings.DATABASE_URL.replace("+asyncpg", "+psycopg2")
sync_engine = create_engine(SYNC_DATABASE_URL, echo=True)
SyncSession = sessionmaker(sync_engine, expire_on_commit=False)


# Base class for all our models (User, Document, etc.)
# Every model inherits from this → SQLAlchemy knows to track it
class Base(DeclarativeBase):
    pass
