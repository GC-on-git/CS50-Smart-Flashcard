"""
Statistics router endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services import statistics as stats_service

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get("/overview", response_model=Dict[str, Any])
async def get_statistics_overview(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get overall statistics for the current user.
    
    Returns:
        Dictionary with:
        - total_cards: Total number of cards
        - total_decks: Total number of decks
        - total_reviews: Total number of reviews
        - mastery_rate: Percentage of cards mastered
        - cards_due: Number of cards due for review
        - mastered_cards: Number of mastered cards
    """
    return stats_service.get_user_statistics(db, current_user.id)


@router.get("/decks", response_model=List[Dict[str, Any]])
async def get_decks_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for all decks owned by the current user.
    
    Returns:
        List of deck statistics dictionaries
    """
    return stats_service.get_all_decks_statistics(db, current_user.id)


@router.get("/decks/{deck_id}", response_model=Dict[str, Any])
async def get_deck_statistics(
    deck_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get statistics for a specific deck.
    
    Args:
        deck_id: Deck ID
        
    Returns:
        Dictionary with deck statistics
        
    Raises:
        HTTPException: If deck not found or not owned by user
    """
    stats = stats_service.get_deck_statistics(db, deck_id, current_user.id)
    if not stats:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deck not found"
        )
    return stats


@router.get("/reviews-timeline", response_model=List[Dict[str, Any]])
async def get_reviews_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get review activity over time.
    
    Args:
        days: Number of days to look back (1-365)
        
    Returns:
        List of dictionaries with date and review count
    """
    return stats_service.get_reviews_timeline(db, current_user.id, days)


@router.get("/difficult-cards", response_model=List[Dict[str, Any]])
async def get_difficult_cards(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of cards to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get cards with lowest ease factors (most difficult).
    
    Args:
        limit: Maximum number of cards to return (1-100)
        
    Returns:
        List of card dictionaries with deck info
    """
    return stats_service.get_difficult_cards(db, current_user.id, limit)

