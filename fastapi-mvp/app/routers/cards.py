"""
Card router endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.card import CardCreate, CardUpdate, CardResponse
from app.services.crud_cards import (
    get_card, get_cards, create_card, update_card, delete_card
)

router = APIRouter(prefix="/decks/{deck_id}/cards", tags=["cards"])

@router.post("", response_model=CardResponse, status_code=status.HTTP_201_CREATED)
async def create_card_endpoint(
    deck_id: int,
    card: CardCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Add a new card to a deck.
    
    Creates a new flashcard with front and back text in the specified deck.
    The deck must be owned by the current authenticated user.
    
    Args:
        deck_id: Deck ID
        card: Card creation data (front, back)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Created card information
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    db_card = create_card(
        db=db,
        card=card,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return db_card

@router.get("", response_model=List[CardResponse])
async def list_cards(
    deck_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    query: Optional[str] = Query(None, description="Search query for front/back content"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List all cards in a deck with optional search/filter.
    
    Returns a paginated list of cards in the specified deck.
    Supports filtering by front or back content using the query parameter.
    Only returns cards from decks owned by the current user.
    
    Args:
        deck_id: Deck ID
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (1-100)
        query: Optional search query to filter cards by front/back content
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CardResponse]: List of card objects
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    cards = get_cards(
        db=db,
        deck_id=deck_id,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        query=query
    )
    # If deck doesn't exist or user doesn't own it, get_cards returns empty list
    # We should verify deck exists
    from app.services.crud_decks import get_deck
    deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck and not cards:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return cards

@router.get("/{card_id}", response_model=CardResponse)
async def get_card_endpoint(
    deck_id: int,
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get details of a specific card.
    
    Returns detailed information about a single card.
    Only returns cards from decks owned by the current user.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Card information
        
    Raises:
        HTTPException: If card or deck not found or not owned by user
    """
    db_card = get_card(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return db_card

@router.put("/{card_id}", response_model=CardResponse)
async def update_card_endpoint(
    deck_id: int,
    card_id: int,
    card_update: CardUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update a card.
    
    Updates the front and/or back text of a card.
    Only cards in decks owned by the current user can be updated.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        card_update: Card update data (front, back)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Updated card information
        
    Raises:
        HTTPException: If card not found or not owned by user
    """
    db_card = update_card(
        db=db,
        card_id=card_id,
        card_update=card_update,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return db_card

@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card_endpoint(
    deck_id: int,
    card_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a card.
    
    Permanently deletes a card from a deck.
    Only cards in decks owned by the current user can be deleted.
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        current_user: Current authenticated user
        db: Database session
        
    Raises:
        HTTPException: If card not found or not owned by user
    """
    success = delete_card(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    return None

