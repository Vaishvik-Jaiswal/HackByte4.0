from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

import logging

# Adjust DATABASE_URL if it's not async (replace postgresql:// with postgresql+asyncpg://)
DATABASE_URL = settings.DATABASE_URL
engine = None

if DATABASE_URL and DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    # Fallback to SQLite if no valid Postgres URL is provided or if it's missing
    ASYNC_DATABASE_URL = "sqlite+aiosqlite:///./auth_system.db"
    print("WARNING: PostgreSQL URL not found or invalid. Falling back to SQLite.")

# Create the engine
engine = create_async_engine(ASYNC_DATABASE_URL, echo=True)

# For SQLite, we might need a specific connect_args for threading, though not strictly required for async
if ASYNC_DATABASE_URL.startswith("sqlite"):
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=True, connect_args={"check_same_thread": False})
AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
