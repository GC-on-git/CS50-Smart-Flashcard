"""
Card router endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.card import CardCreate, CardUpdate, CardResponse, CardReview
from app.services.crud_cards import (
    get_card, get_cards, create_card, update_card, delete_card,
    review_card, get_due_cards, get_due_cards_count
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

@router.get("/due", response_model=List[CardResponse])
async def get_due_cards_endpoint(
    deck_id: int,
    limit: int = Query(100, ge=1, le=100, description="Maximum number of cards to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get cards that are due for review.
    
    Returns cards that have never been reviewed (next_review is None)
    or cards whose next_review date has passed.
    
    Args:
        deck_id: Deck ID
        limit: Maximum number of cards to return (1-100)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CardResponse]: List of cards due for review
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    cards = get_due_cards(
        db=db,
        deck_id=deck_id,
        user_id=current_user.id,
        limit=limit
    )
    
    # Verify deck exists
    from app.services.crud_decks import get_deck
    deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    return cards

@router.get("/due/count")
async def get_due_cards_count_endpoint(
    deck_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the count of cards due for review in a deck.
    
    Args:
        deck_id: Deck ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Dictionary with count of due cards
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    # Verify deck exists
    from app.services.crud_decks import get_deck
    deck = get_deck(db=db, deck_id=deck_id, user_id=current_user.id)
    if not deck:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    
    count = get_due_cards_count(
        db=db,
        deck_id=deck_id,
        user_id=current_user.id
    )
    
    return {"deck_id": deck_id, "due_count": count}

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

@router.post("/{card_id}/review", response_model=CardResponse)
async def review_card_endpoint(
    deck_id: int,
    card_id: int,
    review: CardReview,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Review a card and update its scheduling using SM-2 algorithm.
    
    Submits a review quality rating (0-5) for a card and updates its
    spaced repetition schedule accordingly.
    
    Quality ratings:
    - 0: Complete blackout
    - 1: Incorrect response, but remembered
    - 2: Incorrect response, but with serious difficulty
    - 3: Correct response, but with difficulty
    - 4: Correct response after hesitation
    - 5: Perfect response
    
    Args:
        deck_id: Deck ID
        card_id: Card ID
        review: Review data containing quality (0-5)
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        CardResponse: Updated card with new scheduling information
        
    Raises:
        HTTPException: If card not found, quality invalid, or not owned by user
    """
    if review.quality < 0 or review.quality > 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quality must be between 0 and 5"
        )
    
    db_card = review_card(
        db=db,
        card_id=card_id,
        deck_id=deck_id,
        user_id=current_user.id,
        quality=review.quality
    )
    
    if db_card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Card not found"
        )
    
    return db_card

