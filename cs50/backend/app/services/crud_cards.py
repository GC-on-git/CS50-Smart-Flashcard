"""
Card CRUD operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from app.models.card import Card
from app.models.deck import Deck
from app.schemas.card import CardCreate, CardUpdate
from app.services.scheduling import update_card_schedule, get_cards_due_for_review, get_cards_due_count

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
    # Verify deck ownership
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
    # Verify deck ownership
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
            or_(
                Card.front.ilike(search_term),
                Card.back.ilike(search_term)
            )
        )
    
    return base_query.order_by(Card.created_at.desc()).offset(skip).limit(limit).all()

def create_card(db: Session, card: CardCreate, deck_id: int, user_id: int) -> Optional[Card]:
    """
    Create a new card in a deck.
    
    Args:
        db: Database session
        card: Card creation data
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        Card: Created card object, None if deck not found or not owned by user
    """
    # Verify deck ownership
    deck = db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()
    
    if not deck:
        return None
    
    db_card = Card(**card.model_dump(), deck_id=deck_id)
    db.add(db_card)
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
    Record a card review and update its scheduling.
    
    Args:
        db: Database session
        card_id: Card ID
        deck_id: Deck ID
        user_id: Owner user ID
        quality: Review quality (0-5)
            - 0: Complete blackout
            - 1: Incorrect response, but remembered
            - 2: Incorrect response, but with serious difficulty
            - 3: Correct response, but with difficulty
            - 4: Correct response after hesitation
            - 5: Perfect response
        
    Returns:
        Card: Updated card object, None if not found or not owned by user
    """
    db_card = get_card(db, card_id, deck_id, user_id)
    if not db_card:
        return None
    
    return update_card_schedule(db, db_card, quality)

def get_due_cards(
    db: Session,
    deck_id: int,
    user_id: int,
    limit: int = 100
) -> List[Card]:
    """
    Get cards that are due for review.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        limit: Maximum number of cards to return
        
    Returns:
        List[Card]: List of cards due for review
    """
    return get_cards_due_for_review(db, deck_id, user_id, limit)

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

