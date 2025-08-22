"""
Database initialization and session management
Clean database setup with proper error handling
"""

import logging
from contextlib import contextmanager
from sqlmodel import SQLModel, create_engine as sqlmodel_create_engine, Session
from .config import settings
from .models import init_database

logger = logging.getLogger(__name__)

def get_engine():
    """Create database engine with proper configuration"""
    try:
        engine = sqlmodel_create_engine(
            settings.DATABASE_URL,
            echo=settings.DEBUG,  # Show SQL queries in debug mode
            pool_pre_ping=True,   # Verify connections before use
            pool_recycle=300,     # Recycle connections every 5 minutes
            pool_size=10,         # Connection pool size
            max_overflow=20       # Maximum overflow connections
        )
        return engine
    except Exception as e:
        logger.error(f"Failed to create database engine: {e}")
        raise

@contextmanager
def get_session():
    """Context-managed database session with proper error handling"""
    engine = get_engine()
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        session.rollback()
        raise
    finally:
        session.close()

def init_db():
    """Initialize database tables"""
    try:
        logger.info("Initializing database...")
        
        # Create all tables
        init_database()
        
        logger.info("Database initialized successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

def check_database_connection():
    """Check if database is accessible"""
    try:
        engine = get_engine()
        with Session(engine) as session:
            # Simple query to test connection
            session.exec("SELECT 1").first()
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False

def get_database_stats():
    """Get database statistics"""
    try:
        engine = get_engine()
        with Session(engine) as session:
            from .models import User, SessionState, Message, Character
            
            stats = {
                "total_users": session.exec("SELECT COUNT(*) FROM users").first() or 0,
                "total_sessions": session.exec("SELECT COUNT(*) FROM sessions").first() or 0,
                "total_messages": session.exec("SELECT COUNT(*) FROM messages").first() or 0,
                "total_characters": session.exec("SELECT COUNT(*) FROM characters").first() or 0,
                "active_sessions": session.exec("SELECT COUNT(*) FROM sessions WHERE is_active = 1").first() or 0
            }
            
            return stats
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {"error": str(e)}
