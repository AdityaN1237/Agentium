"""
MongoDB Database Connection and Utilities.
Uses Motor for async MongoDB operations.
"""
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.server_api import ServerApi
from typing import Optional
import logging
import certifi

from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database connection manager."""
    
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None
    
    @classmethod
    async def connect(cls):
        """Establish connection to MongoDB."""
        try:
            cls.client = AsyncIOMotorClient(
                settings.MONGODB_URL,
                server_api=ServerApi('1'),
                tlsCAFile=certifi.where()
            )
            cls.db = cls.client[settings.DATABASE_NAME]
            
            # Verify connection
            await cls.client.admin.command('ping')
            logger.info(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
            
            # Create indexes for better performance
            await cls._create_indexes()
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    @classmethod
    async def disconnect(cls):
        """Close MongoDB connection."""
        if cls.client:
            cls.client.close()
            logger.info("🔌 Disconnected from MongoDB")
    
    @classmethod
    async def _create_indexes(cls):
        """Create database indexes for optimal query performance."""
        try:
            # Candidates collection indexes
            await cls.db.candidates.create_index("email", unique=True)
            await cls.db.candidates.create_index("skills")
            await cls.db.candidates.create_index("preferences")
            
            # Jobs collection indexes
            await cls.db.jobs.create_index("title")
            await cls.db.jobs.create_index("required_skills")
            await cls.db.jobs.create_index("company")
            

            logger.info("📊 Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"Index creation warning: {e}")
    
    @classmethod
    def get_db(cls) -> AsyncIOMotorDatabase:
        """Get database instance."""
        if cls.db is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")
        return cls.db


# Convenience function
def get_database() -> AsyncIOMotorDatabase:
    """Dependency injection for database access."""
    return Database.get_db()
