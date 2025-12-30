"""
Card CRUD operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional, Dict, Any
from app.models.card import Card, CardOption, FlashcardReview
from app.models.deck import Deck
from app.schemas.card import CardCreate, CardUpdate
from app.services.scheduling import (
    update_card_schedule, 
    get_cards_due_for_review, 
    get_cards_due_count,
    update_card_schedule_from_response
)
from app.services.streaks import update_session_streak, get_user_streaks, update_daily_streak_on_review
from app.core.config import settings

def get_card(db: Session, card_id: int, deck_id: int, user_id: int) -> Optional[Card]:
    """
    Get a card by ID, ensuring it belongs to a deck owned by the user.
    
    Args:
        db: Database session
        card_id: Card ID
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        Card: Card object if found and owned by user, None otherwise
    """
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return None
    
    return db.query(Card).filter(
        Card.id == card_id,
        Card.deck_id == deck_id
    ).first()

def get_cards(
    db: Session,
    deck_id: int,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    query: Optional[str] = None
) -> List[Card]:
    """
    Get all cards in a deck with optional search/filter.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        query: Optional search query to filter by front/back content
        
    Returns:
        List[Card]: List of card objects
    """
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return []
    
    base_query = db.query(Card).filter(Card.deck_id == deck_id)
    
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            Card.front.ilike(search_term)
        )
    
    return base_query.order_by(Card.created_at.desc()).offset(skip).limit(limit).all()

def create_card(db: Session, card: CardCreate, deck_id: int, user_id: int) -> Optional[Card]:
    """
    Create a new MCQ card in a deck with options.
    
    Args:
        db: Database session
        card: Card creation data (must include options)
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        Card: Created card object with options, None if deck not found or not owned by user
    """
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return None
    
    card_data = card.model_dump()
    options_data = card_data.pop('options', [])
    
    if len(options_data) != 4:
        raise ValueError("Card must have exactly 4 options")
    
    correct_count = sum(1 for opt in options_data if opt.get('is_correct', False))
    if correct_count != 1:
        raise ValueError("Card must have exactly 1 correct option")
    
    db_card = Card(
        front=card_data.get('front', ''),
        explanation=card_data.get('explanation', ''),
        deck_id=deck_id
    )
    db.add(db_card)
    db.flush()
    
    for idx, option_data in enumerate(options_data):
        option = CardOption(
            card_id=db_card.id,
            text=option_data['text'],
            is_correct=option_data['is_correct'],
            order=idx
        )
        db.add(option)
    
    db.commit()
    db.refresh(db_card)
    return db_card

def update_card(
    db: Session,
    card_id: int,
    card_update: CardUpdate,
    deck_id: int,
    user_id: int
) -> Optional[Card]:
    """
    Update a card.
    
    Args:
        db: Database session
        card_id: Card ID
        card_update: Card update data
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        Card: Updated card object, None if not found or not owned by user
    """
    db_card = get_card(db, card_id, deck_id, user_id)
    if not db_card:
        return None
    
    update_data = card_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_card, key, value)
    
    db.commit()
    db.refresh(db_card)
    return db_card

def delete_card(db: Session, card_id: int, deck_id: int, user_id: int) -> bool:
    """
    Delete a card.
    
    Args:
        db: Database session
        card_id: Card ID
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        bool: True if deleted, False if not found or not owned by user
    """
    db_card = get_card(db, card_id, deck_id, user_id)
    if not db_card:
        return False
    
    db.delete(db_card)
    db.commit()
    return True

def review_card(
    db: Session,
    card_id: int,
    deck_id: int,
    user_id: int,
    quality: int
) -> Optional[Card]:
    """
    Record a card review and update its scheduling (legacy method).
    Use submit_answer() for new MCQ format.
    
    Args:
        db: Database session
        card_id: Card ID
        deck_id: Deck ID
        user_id: Owner user ID
        quality: Review quality (1-5)
        
    Returns:
        Card: Updated card object, None if not found or not owned by user
    """
    db_card = get_card(db, card_id, deck_id, user_id)
    if not db_card:
        return None
    
    return update_card_schedule(db, db_card, quality)


def submit_answer(
    db: Session,
    card_id: int,
    deck_id: int,
    user_id: int,
    selected_option_id: int,
    response_time_ms: int
) -> Optional[Dict[str, Any]]:
    """
    Submit an answer for an MCQ card and process the review.
    
    Args:
        db: Database session
        card_id: Card ID
        deck_id: Deck ID
        user_id: User ID (reviewer, not necessarily owner)
        selected_option_id: ID of the selected option
        response_time_ms: Response time in milliseconds
        
    Returns:
        Dictionary with:
        - correct: bool
        - correct_option_id: int
        - explanation: str
        - updated_card: dict with SM-2 values
        - streaks: dict with session_streak and daily_streak
        None if card/option not found
    """
    db_card = db.query(Card).filter(
        Card.id == card_id,
        Card.deck_id == deck_id
    ).first()
    
    if not db_card:
        return None
    
    selected_option = db.query(CardOption).filter(
        CardOption.id == selected_option_id,
        CardOption.card_id == card_id
    ).first()
    
    if not selected_option:
        return None
    
    correct_option = db.query(CardOption).filter(
        CardOption.card_id == card_id,
        CardOption.is_correct == True
    ).first()
    
    if not correct_option:
        return None
    
    correct = selected_option.is_correct
    
    updated_card, quality = update_card_schedule_from_response(
        db, db_card, correct, response_time_ms
    )
    
    review = FlashcardReview(
        card_id=card_id,
        user_id=user_id,
        selected_option_id=selected_option_id if correct else None,
        correct=correct,
        response_time_ms=response_time_ms,
        sm2_quality=quality
    )
    db.add(review)
    
    session_streak = update_session_streak(db, user_id, correct)
    daily_streak = update_daily_streak_on_review(db, user_id)
    
    streaks = {
        "current_session_streak": session_streak,
        "daily_streak": daily_streak
    }
    
    db.commit()
    
    return {
        "correct": correct,
        "correct_option_id": correct_option.id,
        "explanation": db_card.explanation or "",
        "updated_card": {
            "ease_factor": updated_card.ease_factor,
            "interval": updated_card.interval,
            "repetitions": updated_card.repetitions,
            "next_review": updated_card.next_review.isoformat() if updated_card.next_review else None
        },
        "streaks": {
            "current_session_streak": session_streak,
            "daily_streak": streaks["daily_streak"]
        }
    }

def get_due_cards(
    db: Session,
    deck_id: int,
    user_id: int,
    limit: int = 100,
    mode: Optional[str] = None
) -> List[Card]:
    """
    Get cards that are due for review.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        limit: Maximum number of cards to return
        mode: Optional study mode. 'hard' filters cards with ease_factor < 2.0
        
    Returns:
        List[Card]: List of cards due for review
    """
    cards = get_cards_due_for_review(db, deck_id, user_id, limit)
    
    if mode == 'hard':
        cards = [card for card in cards if card.ease_factor < 2.0]
    
    return cards

def get_due_cards_count(
    db: Session,
    deck_id: int,
    user_id: int
) -> int:
    """
    Get the count of cards due for review.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        int: Number of cards due for review
    """
    return get_cards_due_count(db, deck_id, user_id)


def bulk_delete_cards(
    db: Session,
    deck_id: int,
    card_ids: List[int],
    user_id: int
) -> bool:
    """
    Bulk delete cards.
    
    Args:
        db: Database session
        deck_id: Deck ID
        card_ids: List of card IDs to delete
        user_id: Owner user ID
        
    Returns:
        bool: True if all cards deleted, False if deck not found or not owned by user
    """
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return False
    
    cards = db.query(Card).filter(
        Card.id.in_(card_ids),
        Card.deck_id == deck_id
    ).all()
    
    for card in cards:
        db.delete(card)
    
    db.commit()
    return True


def duplicate_card(
    db: Session,
    deck_id: int,
    card_id: int,
    user_id: int
) -> Optional[Card]:
    """
    Duplicate a card with all its options.
    
    Args:
        db: Database session
        deck_id: Deck ID
        card_id: Card ID to duplicate
        user_id: Owner user ID
        
    Returns:
        Card: Duplicated card object, None if card not found or not owned by user
    """
    original_card = get_card(db, card_id, deck_id, user_id)
    if not original_card:
        return None
    
    new_card = Card(
        front=original_card.front,
        explanation=original_card.explanation,
        deck_id=deck_id,
        ease_factor=2.5,
        interval=0,
        repetitions=0,
        next_review=None
    )
    db.add(new_card)
    db.flush()
    
    original_options = db.query(CardOption).filter(
        CardOption.card_id == card_id
    ).order_by(CardOption.order).all()
    
    for orig_option in original_options:
        new_option = CardOption(
            card_id=new_card.id,
            text=orig_option.text,
            is_correct=orig_option.is_correct,
            order=orig_option.order
        )
        db.add(new_option)
    
    db.commit()
    db.refresh(new_card)
    return new_card

