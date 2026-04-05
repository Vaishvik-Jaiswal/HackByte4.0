import asyncio
import logging
import sys
from sqlalchemy import text
from app.database.session import engine
from app.database.base import Base
from app.models.user import User, OAuth
from app.models.email import Email

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("db-reset")

async def reset_db():
    logger.info("Starting database reset...")
    try:
        async with engine.begin() as conn:
            # Drop tables with CASCADE to ensure all constraints are handled
            logger.info("Dropping existing tables (users, oauth, emails, processed_emails)...")
            await conn.execute(text("DROP TABLE IF EXISTS relay_contexts CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS processed_emails CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS emails CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS oauth CASCADE;"))
            await conn.execute(text("DROP TABLE IF EXISTS users CASCADE;"))
            
            # Recreate all tables
            logger.info("Recreating tables from modern models...")
            await conn.run_sync(Base.metadata.create_all)
            
        logger.info("DATABASE RESET SUCCESSFULLY!")
        logger.info("You can now restart your backend and register a new account.")
    except Exception as e:
        logger.error(f"DATABASE RESET FAILED: {e}")

if __name__ == "__main__":
    asyncio.run(reset_db())
