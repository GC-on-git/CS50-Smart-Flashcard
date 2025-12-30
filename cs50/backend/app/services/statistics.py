"""
Statistics calculation service
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, case
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from app.models.card import Card, FlashcardReview
from app.models.deck import Deck
from app.models.user import User


def get_user_statistics(db: Session, user_id: int) -> Dict[str, Any]:
    """
    Get overall statistics for a user.
    
    Returns:
        Dictionary with:
        - total_cards: Total number of cards across all decks
        - total_decks: Total number of decks
        - total_reviews: Total number of reviews
        - mastery_rate: Percentage of cards with ease_factor >= 2.5
        - cards_due: Number of cards due for review
    """
    total_decks = db.query(Deck).filter(Deck.owner_id == user_id).count()
    
    total_cards = db.query(Card).join(Deck).filter(Deck.owner_id == user_id).count()
    
    total_reviews = db.query(FlashcardReview).filter(FlashcardReview.user_id == user_id).count()
    
    mastered_cards = db.query(Card).join(Deck).filter(
        and_(
            Deck.owner_id == user_id,
            Card.ease_factor >= 2.5
        )
    ).count()
    
    mastery_rate = (mastered_cards / total_cards * 100) if total_cards > 0 else 0
    
    now = datetime.now(timezone.utc)
    cards_due = db.query(Card).join(Deck).filter(
        and_(
            Deck.owner_id == user_id,
            or_(
                Card.next_review.is_(None),
                Card.next_review <= now
            )
        )
    ).count()
    
    return {
        "total_cards": total_cards,
        "total_decks": total_decks,
        "total_reviews": total_reviews,
        "mastery_rate": round(mastery_rate, 2),
        "cards_due": cards_due,
        "mastered_cards": mastered_cards
    }


def get_deck_statistics(db: Session, deck_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """
    Get statistics for a specific deck.
    
    Returns:
        Dictionary with deck statistics or None if deck not found
    """
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return None
    
    total_cards = db.query(Card).filter(Card.deck_id == deck_id).count()
    
    mastered_cards = db.query(Card).filter(
        and_(
            Card.deck_id == deck_id,
            Card.ease_factor >= 2.5
        )
    ).count()
    
    difficult_cards = db.query(Card).filter(
        and_(
            Card.deck_id == deck_id,
            Card.ease_factor < 2.0
        )
    ).count()
    
    now = datetime.now(timezone.utc)
    cards_due = db.query(Card).filter(
        and_(
            Card.deck_id == deck_id,
            or_(
                Card.next_review.is_(None),
                Card.next_review <= now
            )
        )
    ).count()
    
    total_reviews = db.query(FlashcardReview).join(Card).filter(
        Card.deck_id == deck_id
    ).count()
    
    mastery_rate = (mastered_cards / total_cards * 100) if total_cards > 0 else 0
    
    avg_ease = db.query(func.avg(Card.ease_factor)).filter(
        Card.deck_id == deck_id
    ).scalar() or 0
    
    return {
        "deck_id": deck_id,
        "deck_title": deck.title,
        "total_cards": total_cards,
        "mastered_cards": mastered_cards,
        "difficult_cards": difficult_cards,
        "cards_due": cards_due,
        "total_reviews": total_reviews,
        "mastery_rate": round(mastery_rate, 2),
        "average_ease_factor": round(float(avg_ease), 2)
    }


def get_reviews_timeline(
    db: Session,
    user_id: int,
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Get review activity over time.
    
    Args:
        db: Database session
        user_id: User ID
        days: Number of days to look back
        
    Returns:
        List of dictionaries with date and review count
    """
    from sqlalchemy import cast, Date
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    reviews = db.query(
        func.date(FlashcardReview.timestamp).label('date'),
        func.count(FlashcardReview.id).label('count')
    ).filter(
        and_(
            FlashcardReview.user_id == user_id,
            FlashcardReview.timestamp >= start_date
        )
    ).group_by(
        func.date(FlashcardReview.timestamp)
    ).order_by(
        func.date(FlashcardReview.timestamp)
    ).all()
    
    result = []
    for review in reviews:
        date_val = review.date
        if isinstance(date_val, datetime):
            date_str = date_val.date().isoformat()
        elif hasattr(date_val, 'isoformat'):
            date_str = date_val.isoformat()
        else:
            date_str = str(date_val)
        result.append({
            "date": date_str,
            "count": review.count
        })
    
    return result


def get_difficult_cards(
    db: Session,
    user_id: int,
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    Get cards with lowest ease factors.
    
    Args:
        db: Database session
        user_id: User ID
        limit: Maximum number of cards to return
        
    Returns:
        List of card dictionaries with deck info
    """
    cards = db.query(Card, Deck).join(Deck).filter(
        and_(
            Deck.owner_id == user_id,
            Card.ease_factor < 2.5
        )
    ).order_by(
        Card.ease_factor.asc()
    ).limit(limit).all()
    
    result = []
    for card, deck in cards:
        result.append({
            "card_id": card.id,
            "deck_id": card.deck_id,
            "deck_title": deck.title,
            "front": card.front,
            "ease_factor": float(card.ease_factor),
            "interval": card.interval,
            "repetitions": card.repetitions,
            "next_review": card.next_review.isoformat() if card.next_review else None
        })
    
    return result


def get_all_decks_statistics(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    Get statistics for all decks owned by user.
    
    Returns:
        List of deck statistics dictionaries
    """
    decks = db.query(Deck).filter(Deck.owner_id == user_id).all()
    
    result = []
    for deck in decks:
        stats = get_deck_statistics(db, deck.id, user_id)
        if stats:
            result.append(stats)
    
    return result

