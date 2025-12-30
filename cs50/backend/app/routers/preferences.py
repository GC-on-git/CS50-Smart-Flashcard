"""
User preferences router endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.schemas.user_preferences import UserPreferencesResponse, UserPreferencesUpdate
from app.services.preferences import get_or_create_user_preferences, update_user_preferences

router = APIRouter(prefix="/preferences", tags=["preferences"])


@router.get("", response_model=UserPreferencesResponse)
async def get_preferences(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user preferences.
    
    Returns user preferences, creating defaults if they don't exist.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserPreferencesResponse: User preferences
    """
    preferences = get_or_create_user_preferences(db, current_user.id)
    return preferences


@router.put("", response_model=UserPreferencesResponse)
async def update_preferences(
    preferences_update: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user preferences.
    
    Updates user preferences with provided values.
    Creates preferences with defaults if they don't exist.
    
    Args:
        preferences_update: Preferences update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        UserPreferencesResponse: Updated user preferences
    """
    if preferences_update.theme is not None and preferences_update.theme not in ['light', 'dark', 'auto']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Theme must be 'light', 'dark', or 'auto'"
        )
    
    if preferences_update.font_size is not None and preferences_update.font_size not in ['small', 'medium', 'large']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Font size must be 'small', 'medium', or 'large'"
        )
    
    preferences = update_user_preferences(db, current_user.id, preferences_update)
    if preferences is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update preferences"
        )
    
    return preferences
