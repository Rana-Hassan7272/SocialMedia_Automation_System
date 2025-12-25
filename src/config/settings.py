"""
Configuration management for Social Media Automation System.
Uses environment variables with Pydantic validation.
"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # ========================================
    # LLM Configuration (GROQ)
    # ========================================
    groq_api_key: str = Field(..., description="Groq API key")
    groq_model: str = Field(
        default="llama-3.3-70b-versatile",
        description="Groq model to use"
    )
    
    # ========================================
    # Twitter/X API Configuration
    # ========================================
    twitter_api_key: Optional[str] = Field(None, description="Twitter API key")
    twitter_api_secret: Optional[str] = Field(None, description="Twitter API secret")
    twitter_access_token: Optional[str] = Field(None, description="Twitter access token")
    twitter_access_token_secret: Optional[str] = Field(
        None, description="Twitter access token secret"
    )
    twitter_api_version: str = Field(default="v2", description="Twitter API version")
    
    # ========================================
    # Database Configuration
    # ========================================
    database_path: str = Field(
        default="data/social_automation.db",
        description="Path to SQLite database"
    )
    
    # ========================================
    # Application Settings
    # ========================================
    log_level: str = Field(default="INFO", description="Logging level")
    max_tweets_per_query: int = Field(
        default=50,
        description="Maximum tweets to retrieve per query"
    )
    min_engagement_score: int = Field(
        default=10,
        description="Minimum engagement score for filtering"
    )
    top_tweets_count: int = Field(
        default=8,
        description="Number of top tweets for summarization"
    )
    
    @validator("database_path")
    def create_data_directory(cls, v):
        """Ensure data directory exists."""
        db_path = Path(v)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v_upper
    
    def get_database_url(self) -> str:
        """Get SQLAlchemy database URL."""
        return f"sqlite:///{self.database_path}"
    
    def is_twitter_configured(self) -> bool:
        """Check if Twitter API is fully configured."""
        return all([
            self.twitter_api_key,
            self.twitter_api_secret,
            self.twitter_access_token,
            self.twitter_access_token_secret
        ])


# Global settings instance
settings = Settings()
