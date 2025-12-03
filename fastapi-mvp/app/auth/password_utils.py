"""
Password utility functions
"""
from app.core.security import verify_password, get_password_hash

def hash_password(password: str) -> str:
    """
    Hash a plain text password.
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return get_password_hash(password)

def verify_user_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        bool: True if password matches, False otherwise
    """
    return verify_password(plain_password, hashed_password)

