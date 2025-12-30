"""
User router endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.streaks import get_user_streaks

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=dict)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user information including streaks.
    
    Returns detailed information about the currently authenticated user.
    
    Args:
        current_user: Current authenticated user from dependency
        db: Database session
        
    Returns:
        dict: Current user information with streaks
    """
    streaks = get_user_streaks(db, current_user.id)
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "is_active": current_user.is_active,
        "created_at": current_user.created_at,
        "streaks": streaks
    }

@router.get("/streaks", response_model=dict)
async def get_user_streaks_endpoint(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user streak information.
    
    Returns session streak and daily streak for the current user.
    
    Args:
        current_user: Current authenticated user from dependency
        db: Database session
        
    Returns:
        dict: Streak information (current_session_streak, daily_streak)
    """
    return get_user_streaks(db, current_user.id)

