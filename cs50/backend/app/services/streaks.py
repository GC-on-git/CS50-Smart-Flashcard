"""
Streak service for tracking user streaks
"""
from datetime import date, datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.streak import UserStreak
from app.models.deck import Deck
from app.models.card import Card, FlashcardReview
from app.core.config import settings


def get_or_create_user_streak(db: Session, user_id: int) -> UserStreak:
    """
    Get or create a UserStreak record for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        UserStreak object
    """
    streak = db.query(UserStreak).filter(UserStreak.user_id == user_id).first()
    if not streak:
        streak = UserStreak(
            user_id=user_id,
            current_session_streak=0,
            daily_streak=0,
            last_activity_date=None,
            last_session_date=None
        )
        db.add(streak)
        db.commit()
        db.refresh(streak)
    return streak


def update_session_streak(db: Session, user_id: int, correct: bool) -> int:
    """
    Update session streak based on answer correctness.
    Increments on correct, resets to 0 on incorrect.
    
    Args:
        db: Database session
        user_id: User ID
        correct: Whether the answer was correct
        
    Returns:
        Updated session streak value
    """
    streak = get_or_create_user_streak(db, user_id)
    
    if correct:
        streak.current_session_streak += 1
    else:
        streak.current_session_streak = 0
    
    streak.last_session_date = date.today()
    db.commit()
    db.refresh(streak)
    
    return streak.current_session_streak


def update_daily_streak(db: Session, user_id: int, correct: bool) -> int:
    """
    Update daily streak based on answer correctness (legacy function, not used).
    This function is kept for backward compatibility but is not actively used.
    Use update_daily_streak_on_review() instead.
    
    Args:
        db: Database session
        user_id: User ID
        correct: Whether the answer was correct
        
    Returns:
        Updated daily streak value
    """
    streak = get_or_create_user_streak(db, user_id)
    today = date.today()
    
    if streak.last_activity_date != today:
        if streak.last_activity_date:
            days_diff = (today - streak.last_activity_date).days
            if days_diff > 1:
                streak.daily_streak = 0
        else:
            streak.daily_streak = 0
        
        streak.last_activity_date = today
    
    streak.last_activity_date = today
    db.commit()
    db.refresh(streak)
    
    return streak.daily_streak


def check_all_due_cards_completed(db: Session, user_id: int, target_date: date = None) -> bool:
    """
    Check if all due cards in at least one deck were completed on a specific date.
    
    A deck is considered "completed" if all cards that were due at the start of that date
    have been reviewed on that date. If a deck has no due cards, it's considered completed.
    
    Args:
        db: Database session
        user_id: User ID
        target_date: Date to check (defaults to today)
        
    Returns:
        True if all due cards in at least one deck were completed, False otherwise
    """
    if target_date is None:
        target_date = date.today()
    
    decks = db.query(Deck).filter(Deck.owner_id == user_id).all()
    
    if not decks:
        return False
    
    start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    for deck in decks:
        due_cards = db.query(Card).filter(
            and_(
                Card.deck_id == deck.id,
                or_(
                    Card.next_review.is_(None),
                    Card.next_review <= start_datetime
                )
            )
        ).all()
        
        if not due_cards:
            continue
        
        all_completed = True
        for card in due_cards:
            review = db.query(FlashcardReview).filter(
                and_(
                    FlashcardReview.card_id == card.id,
                    FlashcardReview.user_id == user_id,
                    FlashcardReview.timestamp >= start_datetime,
                    FlashcardReview.timestamp <= end_datetime
                )
            ).first()
            
            if not review:
                all_completed = False
                break
        
        if all_completed and len(due_cards) > 0:
            return True
    
    return False


def update_daily_streak_with_completion(db: Session, user_id: int) -> int:
    """
    Update daily streak based on deck completion.
    Maintains/increments streak if all due cards in at least one deck are completed today.
    Breaks streak if not completed and it's a new day.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Updated daily streak value
    """
    streak = get_or_create_user_streak(db, user_id)
    today = date.today()
    
    if streak.last_activity_date != today:
        if streak.last_activity_date:
            days_diff = (today - streak.last_activity_date).days
            if days_diff == 1:
                yesterday_completed = check_all_due_cards_completed(db, user_id, streak.last_activity_date)
                if not yesterday_completed:
                    streak.daily_streak = 0
            elif days_diff > 1:
                streak.daily_streak = 0
        else:
            streak.daily_streak = 0
        
        streak.last_activity_date = today
    
    today_completed = check_all_due_cards_completed(db, user_id, today)
    
    if today_completed:
        if streak.last_activity_date == today:
            pass
    
    db.commit()
    db.refresh(streak)
    
    return streak.daily_streak


def update_daily_streak_on_review(db: Session, user_id: int) -> int:
    """
    Update daily streak when a review is submitted.
    Any card reviewed today maintains/increments the daily streak.
    Simpler logic: reviewing any card today maintains the streak.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Updated daily streak value
    """
    streak = get_or_create_user_streak(db, user_id)
    today = date.today()
    
    if streak.last_activity_date != today:
        if streak.last_activity_date:
            days_diff = (today - streak.last_activity_date).days
            if days_diff == 1:
                yesterday_reviewed = get_daily_review_count(db, user_id, streak.last_activity_date) > 0
                if not yesterday_reviewed:
                    streak.daily_streak = 0
            elif days_diff > 1:
                streak.daily_streak = 0
        else:
            streak.daily_streak = 0
        
        streak.last_activity_date = today
    
    if streak.last_session_date != today:
        streak.daily_streak += 1
        streak.last_session_date = today
    
    db.commit()
    db.refresh(streak)
    
    return streak.daily_streak


def get_daily_review_count(db: Session, user_id: int, target_date: date = None) -> int:
    """
    Get the count of reviews (any review, correct or incorrect) for a user on a specific date.
    
    Args:
        db: Database session
        user_id: User ID
        target_date: Date to check (defaults to today)
        
    Returns:
        Count of reviews on the date
    """
    if target_date is None:
        target_date = date.today()
    
    start_datetime = datetime.combine(target_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_datetime = datetime.combine(target_date, datetime.max.time()).replace(tzinfo=timezone.utc)
    
    count = db.query(FlashcardReview).filter(
        FlashcardReview.user_id == user_id,
        FlashcardReview.timestamp >= start_datetime,
        FlashcardReview.timestamp <= end_datetime
    ).count()
    
    return count


def get_user_streaks(db: Session, user_id: int) -> dict:
    """
    Get current streak values for a user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Dictionary with session_streak and daily_streak
    """
    streak = get_or_create_user_streak(db, user_id)
    
    today = date.today()
    today_reviewed = get_daily_review_count(db, user_id, today) > 0
    
    if today_reviewed and streak.last_session_date != today:
        update_daily_streak_on_review(db, user_id)
        db.refresh(streak)
    
    return {
        "current_session_streak": streak.current_session_streak,
        "daily_streak": streak.daily_streak
    }

