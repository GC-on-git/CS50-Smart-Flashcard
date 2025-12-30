"""
Application Configuration
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
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
        env_file = Path(__file__).resolve().parent.parent.parent / ".env"
        case_sensitive = True

settings = Settings()

