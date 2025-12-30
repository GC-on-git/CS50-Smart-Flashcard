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
    query: Optional[str] = None,
    sort_by: Optional[str] = None,
    order: str = 'asc',
    include_archived: bool = False
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
    
    if not include_archived:
        base_query = base_query.filter(Deck.is_archived == False)
    
    if query:
        search_term = f"%{query}%"
        base_query = base_query.filter(
            or_(
                Deck.title.ilike(search_term),
                Deck.description.ilike(search_term)
            )
        )
    
    if sort_by == 'title':
        order_by = Deck.title.asc() if order == 'asc' else Deck.title.desc()
    elif sort_by == 'created':
        order_by = Deck.created_at.asc() if order == 'asc' else Deck.created_at.desc()
    else:
        order_by = Deck.created_at.desc()
    
    return base_query.order_by(order_by).offset(skip).limit(limit).all()

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


def archive_deck(db: Session, deck_id: int, archive: bool, user_id: int) -> Optional[Deck]:
    """
    Archive or unarchive a deck.
    
    Args:
        db: Database session
        deck_id: Deck ID
        user_id: Owner user ID
        archive: True to archive, False to unarchive
        
    Returns:
        Deck: Updated deck object, None if not found or not owned by user
    """
    db_deck = get_deck(db, deck_id, user_id)
    if not db_deck:
        return None
    
    db_deck.is_archived = archive
    db.commit()
    db.refresh(db_deck)
    return db_deck


def duplicate_deck(db: Session, deck_id: int, user_id: int, new_title: Optional[str] = None) -> Optional[Deck]:
    """
    Duplicate a deck with all its cards.
    
    Args:
        db: Database session
        deck_id: Deck ID to duplicate
        user_id: Owner user ID
        new_title: Optional new title (defaults to "Copy of {original_title}")
        
    Returns:
        Deck: Duplicated deck object, None if original deck not found or not owned by user
    """
    from app.models.card import Card, CardOption
    
    original_deck = get_deck(db, deck_id, user_id)
    if not original_deck:
        return None
    
    new_title = new_title or f"Copy of {original_deck.title}"
    new_deck = Deck(
        title=new_title,
        description=original_deck.description,
        owner_id=user_id,
        is_archived=False
    )
    db.add(new_deck)
    db.flush()
    
    original_cards = db.query(Card).filter(Card.deck_id == deck_id).all()
    for original_card in original_cards:
        new_card = Card(
            front=original_card.front,
            explanation=original_card.explanation,
            deck_id=new_deck.id,
            ease_factor=2.5,
            interval=0,
            repetitions=0,
            next_review=None
        )
        db.add(new_card)
        db.flush()
        
        original_options = db.query(CardOption).filter(
            CardOption.card_id == original_card.id
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
    db.refresh(new_deck)
    return new_deck

