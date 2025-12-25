"""
Card Pydantic schemas
"""
from pydantic import BaseModel, Field, field_validator
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

class CardReview(BaseModel):
    """Schema for card review submission."""
    quality: int = Field(
        ...,
        ge=0,
        le=5,
        description="Review quality rating (0-5): 0=blackout, 1=incorrect remembered, 2=incorrect difficult, 3=correct difficult, 4=correct hesitant, 5=perfect"
    )
    
    @field_validator('quality')
    @classmethod
    def validate_quality(cls, v: int) -> int:
        """Validate quality is in valid range."""
        if not 0 <= v <= 5:
            raise ValueError('Quality must be between 0 and 5')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "quality": 4
            }
        }

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

