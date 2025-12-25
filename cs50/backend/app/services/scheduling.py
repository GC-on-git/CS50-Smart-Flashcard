"""
SM-2 Spaced Repetition Algorithm

This module implements the SuperMemo 2 (SM-2) algorithm for scheduling flashcard reviews.
The algorithm adjusts the review interval based on how well the user remembers each card.

Algorithm details:
- Quality (0-5): User's performance rating
  - 0: Complete blackout
  - 1: Incorrect response, but remembered
  - 2: Incorrect response, but with serious difficulty
  - 3: Correct response, but with difficulty
  - 4: Correct response after hesitation
  - 5: Perfect response

- Ease Factor: Multiplier for interval calculation (starts at 2.5)
- Interval: Days until next review
- Repetitions: Number of successful consecutive reviews
"""
from datetime import datetime, timedelta
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.card import Card
from app.models.deck import Deck


def calculate_sm2_update(
    quality: int,
    ease_factor: float,
    interval: int,
    repetitions: int
) -> Tuple[float, int, int]:
    """
    Calculate new scheduling parameters using SM-2 algorithm.
    
    Args:
        quality: User's performance rating (0-5)
        ease_factor: Current ease factor
        interval: Current interval in days
        repetitions: Current number of repetitions
        
    Returns:
        Tuple of (new_ease_factor, new_interval, new_repetitions)
    """
    # Validate quality
    if quality < 0 or quality > 5:
        raise ValueError("Quality must be between 0 and 5")
    
    # If quality is less than 3, reset the card
    if quality < 3:
        return ease_factor, 1, 0
    
    # Calculate new ease factor
    # EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    # Ensure ease factor doesn't go below 1.3
    if new_ease_factor < 1.3:
        new_ease_factor = 1.3
    
    # Calculate new interval
    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = int(interval * new_ease_factor)
    
    # Increment repetitions
    new_repetitions = repetitions + 1
    
    return new_ease_factor, new_interval, new_repetitions


def update_card_schedule(
    db: Session,
    card: Card,
    quality: int
) -> Card:
    """
    Update a card's scheduling parameters after a review.
    
    Args:
        db: Database session
        card: Card to update
        quality: User's performance rating (0-5)
        
    Returns:
        Updated card object
    """
    new_ease_factor, new_interval, new_repetitions = calculate_sm2_update(
        quality=quality,
        ease_factor=card.ease_factor,
        interval=card.interval,
        repetitions=card.repetitions
    )
    
    # Update card fields
    card.ease_factor = new_ease_factor
    card.interval = new_interval
    card.repetitions = new_repetitions
    card.next_review = datetime.utcnow() + timedelta(days=new_interval)
    # updated_at is handled automatically by SQLAlchemy (onupdate=func.now())
    
    db.commit()
    db.refresh(card)
    
    return card


def get_cards_due_for_review(
    db: Session,
    deck_id: int,
    user_id: int,
    limit: int = 100
) -> list[Card]:
    """
    Get cards that are due for review.
    
    A card is due if:
    - next_review is None (never reviewed)
    - next_review <= current time
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        limit: Maximum number of cards to return
        
    Returns:
        List of cards due for review
    """
    # Verify deck ownership
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return []
    
    now = datetime.utcnow()
    
    # Get cards that are due (next_review is None or <= now)
    cards = db.query(Card).filter(
        and_(
            Card.deck_id == deck_id,
            or_(
                Card.next_review.is_(None),
                Card.next_review <= now
            )
        )
    ).order_by(
        # Prioritize cards that have never been reviewed (next_review is None)
        Card.next_review.nulls_first(),
        # Then by next_review date (oldest first)
        Card.next_review.asc()
    ).limit(limit).all()
    
    return cards


def get_cards_due_count(
    db: Session,
    deck_id: int,
    user_id: int
) -> int:
    """
    Get the count of cards due for review in a deck.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        Number of cards due for review
    """
    # Verify deck ownership
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return 0
    
    now = datetime.utcnow()
    
    count = db.query(Card).filter(
        and_(
            Card.deck_id == deck_id,
            or_(
                Card.next_review.is_(None),
                Card.next_review <= now
            )
        )
    ).count()
    
    return count
