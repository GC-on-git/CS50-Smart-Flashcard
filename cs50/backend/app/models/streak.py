"""
UserStreak model
"""
from sqlalchemy import Column, Integer, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.session import Base


class UserStreak(Base):
    """
    UserStreak model tracking user streak statistics.
    Session streak resets on wrong answer, daily streak requires minimum correct per day.
    """
    __tablename__ = "user_streaks"
    __table_args__ = (
        UniqueConstraint('user_id', name='uq_user_streaks_user_id'),
        {"schema": "flashcards"}
    )
    
    user_id = Column(Integer, ForeignKey("flashcards.users.id", ondelete="CASCADE"), primary_key=True)
    current_session_streak = Column(Integer, default=0)
    daily_streak = Column(Integer, default=0)
    last_activity_date = Column(Date, nullable=True)
    last_session_date = Column(Date, nullable=True)
    
    user = relationship("User", back_populates="streak")
    
    def __repr__(self):
        return f"<UserStreak(user_id={self.user_id}, session_streak={self.current_session_streak}, daily_streak={self.daily_streak})>"

