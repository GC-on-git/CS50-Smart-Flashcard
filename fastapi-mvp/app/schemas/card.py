"""
Card Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class CardBase(BaseModel):
    """Base card schema with common fields."""
    front: str
    back: str

class CardCreate(CardBase):
    """Schema for card creation."""
    pass

class CardUpdate(BaseModel):
    """Schema for card updates."""
    front: Optional[str] = None
    back: Optional[str] = None

class CardResponse(CardBase):
    """Schema for card response."""
    id: int
    deck_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    ease_factor: float
    interval: int
    repetitions: int
    next_review: Optional[datetime] = None
    
    class Config:
        from_attributes = True

