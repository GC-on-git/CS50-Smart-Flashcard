"""
Deck CRUD operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from app.models.deck import Deck
from app.schemas.deck import DeckCreate, DeckUpdate

def get_deck(db: Session, deck_id: int, user_id: int) -> Optional[Deck]:
    """
    Get a deck by ID for a specific user.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        Deck: Deck object if found and owned by user, None otherwise
    """
    return db.query(Deck).filter(
        Deck.id == deck_id,
        Deck.owner_id == user_id
    ).first()

def get_decks(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    query: Optional[str] = None
) -> List[Deck]:
    """
    Get all decks for a user with optional search/filter.
    
    Args:
        db: Database session
        user_id: Owner user ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        query: Optional search query to filter by title/description
        
    Returns:
        List[Deck]: List of deck objects
    """
    base_query = db.query(Deck).filter(Deck.owner_id == user_id)
    
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Deck.title.ilike(search_term),
                Deck.description.ilike(search_term)
            )
        )
    
    return base_query.order_by(Deck.created_at.desc()).offset(skip).limit(limit).all()

def create_deck(db: Session, deck: DeckCreate, user_id: int) -> Deck:
    """
    Create a new deck for a user.
    
    Args:
        db: Database session
        deck: Deck creation data
        user_id: Owner user ID
        
    Returns:
        Deck: Created deck object
    """
    db_deck = Deck(**deck.model_dump(), owner_id=user_id)
    db.add(db_deck)
    db.commit()
    db.refresh(db_deck)
    return db_deck

def update_deck(
    db: Session,
    deck_id: int,
    deck_update: DeckUpdate,
    user_id: int
) -> Optional[Deck]:
    """
    Update a deck.
    
    Args:
        db: Database session
        deck_id: Deck ID
        deck_update: Deck update data
        user_id: Owner user ID
        
    Returns:
        Deck: Updated deck object, None if not found or not owned by user
    """
    db_deck = get_deck(db, deck_id, user_id)
    if not db_deck:
        return None
    
    update_data = deck_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_deck, key, value)
    
    db.commit()
    db.refresh(db_deck)
    return db_deck

def delete_deck(db: Session, deck_id: int, user_id: int) -> bool:
    """
    Delete a deck.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        
    Returns:
        bool: True if deleted, False if not found or not owned by user
    """
    db_deck = get_deck(db, deck_id, user_id)
    if not db_deck:
        return False
    
    db.delete(db_deck)
    db.commit()
    return True

