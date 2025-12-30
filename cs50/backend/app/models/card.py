"""
Card model
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class Card(Base):
    """
    Card model representing a single MCQ flashcard in a deck.
    Includes spaced repetition fields for SM-2 algorithm.
    """
    __tablename__ = "cards"
    __table_args__ = {"schema": "flashcards"}
    
    id = Column(Integer, primary_key=True, index=True)
    front = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)
    deck_id = Column(Integer, ForeignKey("flashcards.decks.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    ease_factor = Column(Float, default=2.5)
    interval = Column(Integer, default=0)
    repetitions = Column(Integer, default=0)
    next_review = Column(DateTime(timezone=True), nullable=True)
    
    deck = relationship("Deck", back_populates="cards")
    options = relationship("CardOption", back_populates="card", cascade="all, delete-orphan", order_by="CardOption.order")
    reviews = relationship("FlashcardReview", back_populates="card", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Card(id={self.id}, deck_id={self.deck_id}, front={self.front[:50]})>"


class CardOption(Base):
    """
    CardOption model representing a single option for an MCQ card.
    Each card has exactly 4 options, with exactly 1 correct option.
    """
    __tablename__ = "card_options"
    __table_args__ = {"schema": "flashcards"}
    
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("flashcards.cards.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    is_correct = Column(Boolean, default=False)
    order = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    card = relationship("Card", back_populates="options")
    reviews = relationship("FlashcardReview", back_populates="selected_option")
    
    def __repr__(self):
        return f"<CardOption(id={self.id}, card_id={self.card_id}, is_correct={self.is_correct})>"


class FlashcardReview(Base):
    """
    FlashcardReview model tracking every review attempt.
    Persists user responses, timing, and SM-2 quality for analytics.
    """
    __tablename__ = "flashcard_reviews"
    __table_args__ = {"schema": "flashcards"}
    
    id = Column(Integer, primary_key=True, index=True)
    card_id = Column(Integer, ForeignKey("flashcards.cards.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("flashcards.users.id", ondelete="CASCADE"), nullable=False, index=True)
    selected_option_id = Column(Integer, ForeignKey("flashcards.card_options.id", ondelete="SET NULL"), nullable=True)
    correct = Column(Boolean, nullable=False)
    response_time_ms = Column(Integer, nullable=False)
    sm2_quality = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    card = relationship("Card", back_populates="reviews")
    user = relationship("User", back_populates="reviews")
    selected_option = relationship("CardOption", back_populates="reviews")
    
    def __repr__(self):
        return f"<FlashcardReview(id={self.id}, card_id={self.card_id}, user_id={self.user_id}, correct={self.correct})>"

