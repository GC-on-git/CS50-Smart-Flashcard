"""
User preferences service
"""
from sqlalchemy.orm import Session
from typing import Optional
from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import UserPreferencesCreate, UserPreferencesUpdate


def get_user_preferences(db: Session, user_id: int) -> Optional[UserPreferences]:
    """
    Get user preferences or return None if not found.
    """
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()


def get_or_create_user_preferences(db: Session, user_id: int) -> UserPreferences:
    """
    Get user preferences or create with defaults if not found.
    """
    preferences = get_user_preferences(db, user_id)
    if preferences is None:
        default_prefs = UserPreferences(
            user_id=user_id,
            theme='dark',
            font_size='medium',
            study_session_preferences=None
        )
        db.add(default_prefs)
        db.commit()
        db.refresh(default_prefs)
        return default_prefs
    return preferences


def create_user_preferences(db: Session, user_id: int, preferences: UserPreferencesCreate) -> UserPreferences:
    """
    Create new user preferences.
    """
    db_preferences = UserPreferences(
        user_id=user_id,
        theme=preferences.theme,
        font_size=preferences.font_size,
        study_session_preferences=preferences.study_session_preferences
    )
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences


def update_user_preferences(
    db: Session,
    user_id: int,
    preferences_update: UserPreferencesUpdate
) -> Optional[UserPreferences]:
    """
    Update user preferences.
    Creates preferences with defaults if they don't exist.
    """
    db_preferences = get_or_create_user_preferences(db, user_id)
    
    if preferences_update.theme is not None:
        db_preferences.theme = preferences_update.theme
    if preferences_update.font_size is not None:
        db_preferences.font_size = preferences_update.font_size
    if preferences_update.study_session_preferences is not None:
        db_preferences.study_session_preferences = preferences_update.study_session_preferences
    
    db.commit()
    db.refresh(db_preferences)
    return db_preferences
