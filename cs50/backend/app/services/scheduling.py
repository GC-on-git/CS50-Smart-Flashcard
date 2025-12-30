"""
SM-2 Spaced Repetition Algorithm

This module implements the SuperMemo 2 (SM-2) algorithm for scheduling flashcard reviews.
The algorithm adjusts the review interval based on how well the user remembers each card.

Algorithm details:
- Quality (1-5): Automatically calculated from correctness and response time
  - 5: Correct + fast response (<5s)
  - 4: Correct + medium response (5-15s)
  - 3: Correct + slow response (>15s)
  - 1: Incorrect response

- Ease Factor: Multiplier for interval calculation (starts at 2.5)
- Interval: Days until next review
- Repetitions: Number of successful consecutive reviews
"""
from datetime import datetime, timedelta, timezone
from typing import Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.models.card import Card
from app.models.deck import Deck
from app.core.config import settings


def calculate_quality_from_response(correct: bool, response_time_ms: int) -> int:
    """
    Calculate SM-2 quality score from correctness and response time.
    
    Args:
        correct: Whether the answer was correct
        response_time_ms: Response time in milliseconds
        
    Returns:
        Quality score (1-5):
        - 5: Correct + fast response (<5s)
        - 4: Correct + medium response (5-15s)
        - 3: Correct + slow response (>15s)
        - 1: Incorrect response
    """
    if not correct:
        return 1
    
    if response_time_ms < settings.FAST_RESPONSE_MS:
        return 5
    elif response_time_ms < settings.MEDIUM_RESPONSE_MS:
        return 4
    else:
        return 3


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
    if quality < 1 or quality > 5:
        raise ValueError("Quality must be between 1 and 5")
    
    if quality < 3:
        return ease_factor, 1, 0
    
    new_ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    if new_ease_factor < 1.3:
        new_ease_factor = 1.3
    
    if repetitions == 0:
        new_interval = 1
    elif repetitions == 1:
        new_interval = 6
    else:
        new_interval = int(interval * new_ease_factor)
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
        quality: SM-2 quality score (1-5)
        
    Returns:
        Updated card object
    """
    new_ease_factor, new_interval, new_repetitions = calculate_sm2_update(
        quality=quality,
        ease_factor=card.ease_factor,
        interval=card.interval,
        repetitions=card.repetitions
    )
    
    card.ease_factor = new_ease_factor
    card.interval = new_interval
    card.repetitions = new_repetitions
    card.next_review = datetime.now(timezone.utc) + timedelta(days=new_interval)
    
    db.commit()
    db.refresh(card)
    
    return card


def update_card_schedule_from_response(
    db: Session,
    card: Card,
    correct: bool,
    response_time_ms: int
) -> Tuple[Card, int]:
    """
    Update a card's scheduling parameters from a response.
    Calculates quality automatically from correctness and response time.
    
    Args:
        db: Database session
        card: Card to update
        correct: Whether the answer was correct
        response_time_ms: Response time in milliseconds
        
    Returns:
        Tuple of (updated card object, quality score)
    """
    quality = calculate_quality_from_response(correct, response_time_ms)
    updated_card = update_card_schedule(db, card, quality)
    return updated_card, quality


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
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return []
    
    now = datetime.now(timezone.utc)
    
    cards = db.query(Card).filter(
        and_(
            Card.deck_id == deck_id,
            or_(
                Card.next_review.is_(None),
                Card.next_review <= now
            )
        )
    ).order_by(
        Card.next_review.nulls_first(),
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
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return 0
    
    now = datetime.now(timezone.utc)
    
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
