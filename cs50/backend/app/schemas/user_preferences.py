"""
UserPreferences Pydantic schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class StudySessionPreferences(BaseModel):
    """Study session preferences."""
    cards_per_session: Optional[int] = Field(None, ge=1, le=200, description="Number of cards per study session")
    auto_advance_delay_ms: Optional[int] = Field(None, ge=0, le=10000, description="Auto-advance delay in milliseconds")


class UserPreferencesBase(BaseModel):
    """Base preferences schema."""
    theme: str = Field(default='dark', description="Theme: 'light', 'dark', or 'auto'")
    font_size: str = Field(default='medium', description="Font size: 'small', 'medium', or 'large'")
    study_session_preferences: Optional[Dict[str, Any]] = Field(None, description="Study session preferences")


class UserPreferencesCreate(UserPreferencesBase):
    """Schema for creating user preferences."""
    pass


class UserPreferencesUpdate(BaseModel):
    """Schema for updating user preferences (all fields optional)."""
    theme: Optional[str] = Field(None, description="Theme: 'light', 'dark', or 'auto'")
    font_size: Optional[str] = Field(None, description="Font size: 'small', 'medium', or 'large'")
    study_session_preferences: Optional[Dict[str, Any]] = Field(None, description="Study session preferences")


class UserPreferencesResponse(UserPreferencesBase):
    """Schema for user preferences response."""
    user_id: int
    
    class Config:
        from_attributes = True
