"""Application configuration management."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Google OAuth Configuration
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24

    # AI Provider Configuration
    AI_PROVIDER: str = "gemini"  # Options: "openai" or "gemini"

    # OpenAI Configuration (only needed if AI_PROVIDER=openai)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Gemini Configuration (only needed if AI_PROVIDER=gemini) - FREE!
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-2.0-flash-lite"  # Fast, free tier model

    # Groq Configuration (only needed if AI_PROVIDER=groq) - FREE!
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Fast, free tier model

    # Application Configuration
    FRONTEND_URL: str = "http://localhost:3000"
    BACKEND_URL: str = "http://localhost:8000"
    ENVIRONMENT: str = "development"

    # Gmail API Scopes
    GMAIL_SCOPES: list = [
        "https://mail.google.com/",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
        "openid"
    ]

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
