"""
Card Pydantic schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime

class CardOptionBase(BaseModel):
    """Base option schema."""
    text: str
    is_correct: bool

class CardOptionCreate(CardOptionBase):
    """Schema for creating an option."""
    pass

class CardOptionResponse(BaseModel):
    """Schema for option response (without is_correct for study mode)."""
    id: int
    text: str
    
    class Config:
        from_attributes = True

class CardBase(BaseModel):
    """Base card schema with common fields."""
    front: str
    explanation: Optional[str] = None

class CardCreate(CardBase):
    """Schema for card creation with options."""
    options: List[CardOptionCreate] = Field(..., min_length=4, max_length=4, description="Exactly 4 options")
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v: List[CardOptionCreate]) -> List[CardOptionCreate]:
        """Validate exactly 1 correct option."""
        correct_count = sum(1 for opt in v if opt.is_correct)
        if correct_count != 1:
            raise ValueError('Card must have exactly 1 correct option')
        return v

class CardUpdate(BaseModel):
    """Schema for card updates."""
    front: Optional[str] = None
    explanation: Optional[str] = None

class CardReview(BaseModel):
    """Schema for card review submission (legacy)."""
    quality: int = Field(
        ...,
        ge=1,
        le=5,
        description="Review quality rating (1-5)"
    )
    
    @field_validator('quality')
    @classmethod
    def validate_quality(cls, v: int) -> int:
        """Validate quality is in valid range."""
        if not 1 <= v <= 5:
            raise ValueError('Quality must be between 1 and 5')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "quality": 4
            }
        }

class AnswerSubmission(BaseModel):
    """Schema for submitting an answer to an MCQ card."""
    selected_option_id: int = Field(..., description="ID of the selected option")
    response_time_ms: int = Field(..., ge=0, description="Response time in milliseconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "selected_option_id": 123,
                "response_time_ms": 3500
            }
        }

class AnswerResponse(BaseModel):
    """Schema for answer submission response."""
    correct: bool
    correct_option_id: int
    explanation: str
    updated_card: dict
    streaks: dict

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
    options: Optional[List[CardOptionResponse]] = None
    
    class Config:
        from_attributes = True

class CardStudyResponse(BaseModel):
    """Schema for card in study mode (without correct answer indicators)."""
    question: str
    options: List[CardOptionResponse]
    time_thresholds: dict
    
    class Config:
        from_attributes = True

class AICardGenerationRequest(BaseModel):
    """Schema for AI card generation request."""
    topic: Optional[str] = Field(None, description="Topic description for card generation")
    num_cards: int = Field(..., ge=1, le=50, description="Number of cards to generate")

class BulkDeleteRequest(BaseModel):
    """Schema for bulk delete request."""
    card_ids: List[int] = Field(..., min_length=1, description="List of card IDs to delete")
