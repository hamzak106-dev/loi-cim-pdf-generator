"""
Database configuration and utilities for Business Acquisition PDF Generator
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from config import settings
from typing import Generator

# Database configuration
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries in debug mode
    pool_pre_ping=True,   # Verify connections before use
    pool_recycle=300      # Recycle connections every 5 minutes
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

def get_db() -> Generator[Session, None, None]:
    """
    Database dependency for FastAPI
    Provides a database session and ensures it's closed after use
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    """
    Create all database tables
    """
    from models import Base
    Base.metadata.create_all(bind=engine)

def drop_tables():
    """
    Drop all database tables (use with caution!)
    """
    from models import Base
    Base.metadata.drop_all(bind=engine)

def get_db_info():
    """
    Get database connection information
    """
    return {
        "database_url": settings.DATABASE_URL.replace(
            settings.DATABASE_URL.split('@')[0].split('//')[1], 
            "***:***"
        ) if '@' in settings.DATABASE_URL else settings.DATABASE_URL,
        "engine_info": str(engine.url),
        "pool_size": engine.pool.size(),
        "checked_out_connections": engine.pool.checkedout(),
    }

class DatabaseManager:
    """
    Database management utilities
    """
    
    @staticmethod
    def init_db():
        """Initialize database with tables"""
        create_tables()
        print("✅ Database tables created successfully!")
    
    @staticmethod
    def reset_db():
        """Reset database (drop and recreate tables)"""
        drop_tables()
        create_tables()
        print("🔄 Database reset completed!")
    
    @staticmethod
    def check_connection():
        """Check database connection"""
        try:
            from sqlalchemy import text
            with engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                return True, "Database connection successful"
        except Exception as e:
            return False, f"Database connection failed: {str(e)}"
