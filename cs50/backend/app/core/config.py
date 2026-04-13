"""
Application Configuration
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PORT: int = 8000
    ALLOWED_ORIGINS: str = "http://localhost:3000"

    DATABASE_URL: str = "postgresql://user:password@localhost/dbname"
    
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GITHUB_CLIENT_ID: Optional[str] = None
    GITHUB_CLIENT_SECRET: Optional[str] = None
    
    AI_API_KEY: Optional[str] = None
    AI_MODEL: str = "openai/gpt-3.5-turbo"
    
    APP_NAME: str = "FastAPI MVP"
    DEBUG: bool = False
    
    FAST_RESPONSE_MS: int = 5000
    MEDIUM_RESPONSE_MS: int = 15000
    
    class Config:
        # Repo layout: <repo>/cs50/backend/app/core/config.py
        # Centralized env: <repo>/.env
        env_file = Path(__file__).resolve().parents[4] / ".env"
        case_sensitive = True
        extra = "ignore"

settings = Settings()

