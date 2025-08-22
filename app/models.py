"""
Database models using SQLModel
Clean, type-safe database models with proper relationships
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, create_engine, Session, select
from pydantic import BaseModel

# Base model for common fields
class TimestampMixin(SQLModel):
    """Mixin for timestamp fields"""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# User model
class User(SQLModel, table=True):
    """User model for storing user information"""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: int = Field(unique=True, index=True, description="Telegram user ID")
    username: Optional[str] = Field(default=None, description="Telegram username")
    first_name: Optional[str] = Field(default=None, description="User's first name")
    last_name: Optional[str] = Field(default=None, description="User's last name")
    is_premium: bool = Field(default=False, description="Telegram Premium status")
    is_verified: bool = Field(default=False, description="Age verification status")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # User preferences
    preferred_language: str = Field(default="en", description="Preferred language")
    character_style: str = Field(default="realistic", description="Preferred character style")
    nsfw_level: int = Field(default=3, description="NSFW content level (1-5)")
    
    # Usage statistics
    total_messages: int = Field(default=0, description="Total messages sent")
    total_characters: int = Field(default=0, description="Total characters created")
    total_images: int = Field(default=0, description="Total images generated")

# Session model for conversation management
class SessionState(SQLModel, table=True):
    """Session state for managing conversation context"""
    __tablename__ = "sessions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.telegram_id", index=True)
    is_active: bool = Field(default=True, description="Whether session is active")
    
    # Character context
    character_id: Optional[int] = Field(default=None, description="Current character ID")
    character_name: Optional[str] = Field(default=None, description="Current character name")
    style: str = Field(default="realistic", description="Character style")
    
    # Conversation context
    context_summary: Optional[str] = Field(default=None, description="Conversation summary")
    message_count: int = Field(default=0, description="Number of messages in session")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)

# Message model for storing conversation messages
class Message(SQLModel, table=True):
    """Message model for storing conversation history"""
    __tablename__ = "messages"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="sessions.id", index=True)
    role: str = Field(description="Message role: user, assistant, system")
    text: str = Field(description="Message content")
    tokens: Optional[int] = Field(default=None, description="Token count")
    meta_data: str = Field(default="{}", description="Additional metadata as JSON string")
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Character model for storing character information
class Character(SQLModel, table=True):
    """Character model for storing character cards"""
    __tablename__ = "characters"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Character name")
    persona: str = Field(description="Character personality")
    boundaries: str = Field(description="Character boundaries")
    scenario: str = Field(description="Character scenario")
    greeting: str = Field(description="Character greeting")
    style: str = Field(description="Character style")
    nsfw_level: int = Field(default=3, description="NSFW level (1-5)")
    tags: str = Field(default="[]", description="Character tags as JSON string")
    image_prompt: Optional[str] = Field(default=None, description="Character image prompt")
    
    # Usage statistics
    usage_count: int = Field(default=0, description="Number of times used")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Audit log model for safety and monitoring
class AuditLog(SQLModel, table=True):
    """Audit log for safety and monitoring"""
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.telegram_id", index=True)
    action: str = Field(description="Action performed")
    content_hash: str = Field(description="Hash of content for privacy")
    result: str = Field(description="Result of action")
    meta_data: str = Field(default="{}", description="Additional metadata as JSON string")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# Pydantic models for API responses
class UserResponse(BaseModel):
    """User response model for API"""
    id: int
    telegram_id: int
    username: Optional[str]
    first_name: Optional[str]
    is_premium: bool
    is_verified: bool
    total_messages: int
    total_characters: int
    total_images: int
    created_at: datetime

class SessionResponse(BaseModel):
    """Session response model for API"""
    id: int
    user_id: int
    is_active: bool
    character_name: Optional[str]
    style: str
    message_count: int
    last_activity: datetime

class MessageResponse(BaseModel):
    """Message response model for API"""
    id: int
    session_id: int
    role: str
    text: str
    tokens: Optional[int]
    created_at: datetime

class CharacterResponse(BaseModel):
    """Character response model for API"""
    id: int
    name: str
    persona: str
    boundaries: str
    scenario: str
    greeting: str
    style: str
    nsfw_level: int
    tags: list
    usage_count: int
    created_at: datetime

# Statistics models
class UserStats(BaseModel):
    """User statistics model"""
    total_messages: int
    total_characters: int
    total_images: int
    average_message_length: float
    most_used_character: Optional[str]
    last_activity: datetime

class SystemStats(BaseModel):
    """System statistics model"""
    total_users: int
    total_sessions: int
    total_messages: int
    total_characters: int
    active_sessions: int
    memory_usage_mb: float
    average_response_time_ms: float

# Database engine and session management
def create_database_engine(database_url: str):
    """Create database engine"""
    return create_engine(
        database_url,
        echo=False,  # Set to True for SQL debugging
        pool_pre_ping=True,
        pool_recycle=300
    )

def get_session():
    """Get database session"""
    from .config import settings
    engine = create_database_engine(settings.DATABASE_URL)
    with Session(engine) as session:
        yield session

def init_database():
    """Initialize database tables"""
    from .config import settings
    engine = create_database_engine(settings.DATABASE_URL)
    SQLModel.metadata.create_all(engine)
