"""
UserPreferences model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base


class UserPreferences(Base):
    """
    UserPreferences model storing user customization settings.
    """
    __tablename__ = "user_preferences"
    __table_args__ = {"schema": "flashcards"}
    
    user_id = Column(Integer, ForeignKey("flashcards.users.id", ondelete="CASCADE"), primary_key=True, index=True)
    theme = Column(String, default='dark')
    font_size = Column(String, default='medium')
    study_session_preferences = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", back_populates="preferences")
    
    def __repr__(self):
        return f"<UserPreferences(user_id={self.user_id}, theme={self.theme})>"
