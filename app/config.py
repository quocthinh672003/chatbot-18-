"""
Configuration management using Pydantic Settings
Centralized configuration with environment variable support
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Telegram Bot Configuration
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot token from @BotFather")
    
    # LLM Backend Configuration (Priority: Venice > Groq > OpenRouter)
    VENICE_API_KEY: str = Field("", description="Venice AI API key (primary LLM backend)")
    GROQ_API_KEY: str = Field("", description="Groq API key (fallback LLM backend)")
    OPENAI_API_KEY: str = Field("", description="OpenAI API key (fallback)")
    
    # Image Generation Configuration (Priority: Venice > Stable Horde)
    VENICE_IMAGE_API_KEY: str = Field("", description="Venice AI image API key (primary)")
    STABLE_HORDE_API_KEY: str = Field("", description="Stable Horde API key (optional, anonymous if empty)")
    
    # Database Configuration
    DATABASE_URL: str = Field("sqlite:///./chatbot.db", description="Database connection URL")
    
    # Redis Configuration (for caching)
    REDIS_URL: str = Field("redis://localhost:6379", description="Redis connection URL")
    
    # Application Configuration
    DEBUG: bool = Field(False, description="Enable debug mode")
    LOG_LEVEL: str = Field("INFO", description="Logging level")
    
    # Memory Configuration
    MAX_RECENT_MESSAGES: int = Field(5, description="Maximum recent messages to keep in context")
    MAX_SUMMARY_LENGTH: int = Field(100, description="Maximum length of conversation summary")
    SUMMARY_THRESHOLD: int = Field(10, description="Number of messages before creating summary")
    
    # Safety Configuration
    AGE_VERIFICATION_REQUIRED: bool = Field(True, description="Require age verification")
    MIN_AGE: int = Field(18, description="Minimum age requirement")
    MAX_RISK_LEVEL: int = Field(3, description="Maximum allowed risk level")
    
    # Performance Configuration
    MAX_RESPONSE_TIME_MS: int = Field(5000, description="Maximum response time in milliseconds")
    MAX_MEMORY_USAGE_MB: int = Field(500, description="Maximum memory usage in MB")
    
    # Image Generation Configuration
    IMAGE_GENERATION_ENABLED: bool = Field(True, description="Enable image generation")
    IMAGE_TIMEOUT_SECONDS: int = Field(120, description="Image generation timeout")
    
    # Webhook Configuration (if using webhooks)
    WEBHOOK_URL: Optional[str] = Field(None, description="Webhook URL for production")
    WEBHOOK_SECRET: str = Field("", description="Webhook secret for security")
    
    # Monitoring Configuration
    ENABLE_METRICS: bool = Field(False, description="Enable metrics collection")
    METRICS_PORT: int = Field(9090, description="Metrics server port")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Global settings instance
settings = Settings()

# Validation on import
def validate_settings():
    """Validate critical settings"""
    if not settings.TELEGRAM_BOT_TOKEN:
        raise ValueError("TELEGRAM_BOT_TOKEN is required")
    
    # Check if at least one LLM backend is configured
    if not any([settings.VENICE_API_KEY, settings.GROQ_API_KEY, settings.OPENAI_API_KEY]):
        print("Warning: No LLM API key configured. Some features may not work.")
    
    # Check if at least one image backend is configured
    if not any([settings.VENICE_IMAGE_API_KEY]):
        print("Warning: No image generation API key configured. Image features may not work.")

# Validate on import
validate_settings()
