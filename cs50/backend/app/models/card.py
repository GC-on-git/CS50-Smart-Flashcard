"""
Card model
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Card(Base):
    """
    Card model representing a single flashcard in a deck.
    Includes spaced repetition fields for future implementation.
    """
    __tablename__ = "cards"
    __table_args__ = {"schema": "flashcards"}
    
    id = Column(Integer, primary_key=True, index=True)
    front = Column(Text, nullable=False)
    back = Column(Text, nullable=False)
    deck_id = Column(Integer, ForeignKey("flashcards.decks.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Spaced repetition fields (for future use)
    ease_factor = Column(Float, default=2.5)
    interval = Column(Integer, default=0)  # days until next review
    repetitions = Column(Integer, default=0)
    next_review = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    deck = relationship("Deck", back_populates="cards")
    
    def __repr__(self):
        return f"<Card(id={self.id}, deck_id={self.deck_id}, front={self.front[:50]})>"

