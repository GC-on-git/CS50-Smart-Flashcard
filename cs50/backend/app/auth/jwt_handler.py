"""
JWT token handler
"""
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.core.config import settings
from app.core.security import create_access_token, decode_access_token

def create_token_pair(user_id: int) -> Dict[str, str]:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_id: User ID to include in token
        
    Returns:
        dict: Dictionary containing access_token and refresh_token
    """
    # Access token (short-lived)
    # JWT spec requires 'sub' to be a string
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=access_token_expires
    )
    
    # Refresh token (long-lived, 7 days)
    refresh_token_expires = timedelta(days=7)
    refresh_token = create_access_token(
        data={"sub": str(user_id), "type": "refresh"},
        expires_delta=refresh_token_expires
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token to verify
        
    Returns:
        dict: Token payload if valid, None otherwise
    """
    return decode_access_token(token)

def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Generate a new access token from a refresh token.
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        str: New access token if refresh token is valid, None otherwise
    """
    payload = verify_token(refresh_token)
    if payload is None:
        return None
    
    token_type = payload.get("type")
    if token_type != "refresh":
        return None
    
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None
    
    # Convert string back to int
    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        return None
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=access_token_expires
    )
    
    return new_access_token

