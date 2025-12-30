"""
Deck router endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.deck import DeckCreate, DeckUpdate, DeckResponse, DeckWithCards
from app.services.crud_decks import (
    get_deck, get_decks, create_deck, update_deck, delete_deck
)

router = APIRouter(prefix="/decks", tags=["decks"])

@router.post("", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def create_deck_endpoint(
    deck: DeckCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new deck for the current user.
    
    Creates a new flashcard deck with title and optional description.
    The deck is automatically associated with the current authenticated user.
    
    Args:
        deck: Deck creation data (title, description)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DeckResponse: Created deck information
    """
    return create_deck(db=db, deck=deck, user_id=current_user.id)

@router.get("", response_model=List[DeckResponse])
async def list_decks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    query: Optional[str] = Query(None, description="Search query for title/description"),
    sort_by: Optional[str] = Query(None, description="Sort by: 'title', 'created', 'due_count'"),
    order: Optional[str] = Query('asc', description="Sort order: 'asc' or 'desc'"),
    include_archived: bool = Query(False, description="Include archived decks"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all decks for the current user with optional search/filter/sort.
    
    Returns a paginated list of decks owned by the current user.
    Supports filtering by title or description using the query parameter.
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        query: Optional search query to filter decks by title/description
        sort_by: Optional sort field ('title', 'created', 'due_count')
        order: Sort order ('asc' or 'desc')
        include_archived: Whether to include archived decks
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[DeckResponse]: List of deck objects
    """
    return get_decks(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        query=query,
        sort_by=sort_by,
        order=order,
        include_archived=include_archived
    )

@router.get("/{deck_id}", response_model=DeckWithCards)
async def get_deck_endpoint(
    deck_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific deck including all cards.
    
    Returns detailed information about a deck including its cards.
    Only returns decks owned by the current user.
    
    Args:
        deck_id: Deck ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DeckWithCards: Deck information with cards
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    db_deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if db_deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    return db_deck

@router.put("/{deck_id}", response_model=DeckResponse)
async def update_deck_endpoint(
    deck_id: int,
    deck_update: DeckUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update title/description of a deck.
    
    Updates the title and/or description of a deck.
    Only the owner of the deck can update it.
    
    Args:
        deck_id: Deck ID
        deck_update: Deck update data (title, description)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DeckResponse: Updated deck information
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    db_deck = update_deck(
        db=db,
        deck_id=deck_id,
        deck_update=deck_update,
        user_id=current_user.id
    )
    if db_deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return db_deck

@router.post("/{deck_id}/archive", response_model=DeckResponse)
async def archive_deck_endpoint(
    deck_id: int,
    archive: bool = Query(True, description="True to archive, False to unarchive"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Archive or unarchive a deck.
    
    Args:
        deck_id: Deck ID
        archive: True to archive, False to unarchive
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DeckResponse: Updated deck
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    from app.services.crud_decks import archive_deck
    deck = archive_deck(db, deck_id, archive, current_user.id)
    if deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return deck

@router.post("/{deck_id}/duplicate", response_model=DeckResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_deck_endpoint(
    deck_id: int,
    new_title: Optional[str] = Query(None, description="Optional new title for the duplicated deck"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Duplicate a deck with all its cards.
    
    Args:
        deck_id: Deck ID to duplicate
        new_title: Optional new title (defaults to "Copy of {original_title}")
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        DeckResponse: Duplicated deck
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    from app.services.crud_decks import duplicate_deck
    deck = duplicate_deck(db, deck_id, current_user.id, new_title)
    if deck is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return deck

@router.delete("/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_deck_endpoint(
    deck_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a deck.
    
    Permanently deletes a deck and all its cards.
    Only the owner of the deck can delete it.
    
    Args:
        deck_id: Deck ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    success = delete_deck(
        db=db,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return None

