"""
Deck Pydantic schemas
"""
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class DeckBase(BaseModel):
    """Base deck schema with common fields."""
    title: str
    description: Optional[str] = None

class DeckCreate(DeckBase):
    """Schema for deck creation."""
    pass

class DeckUpdate(BaseModel):
    """Schema for deck updates."""
    title: Optional[str] = None
    description: Optional[str] = None

class DeckResponse(DeckBase):
    """Schema for deck response."""
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DeckWithCards(DeckResponse):
    """Schema for deck response with cards."""
    cards: List["CardResponse"] = []
    
    class Config:
        from_attributes = True

# Import here to avoid circular imports
from app.schemas.card import CardResponse

DeckWithCards.model_rebuild()

