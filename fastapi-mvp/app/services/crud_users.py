"""
User CRUD operations
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Get user by ID.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Get user by email.
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Get user by username.
    
    Args:
        db: Database session
        username: Username
        
    Returns:
        User: User object if found, None otherwise
    """
    return db.query(User).filter(User.username == username).first()

def create_user(
    db: Session,
    email: str,
    username: str,
    hashed_password: Optional[str] = None,
    oauth_provider: Optional[str] = None,
    oauth_id: Optional[str] = None
) -> User:
    """
    Create a new user.
    
    Args:
        db: Database session
        email: User email
        username: Username
        hashed_password: Hashed password (optional for OAuth users)
        oauth_provider: OAuth provider name (optional)
        oauth_id: OAuth ID (optional)
        
    Returns:
        User: Created user object
    """
    db_user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        oauth_provider=oauth_provider,
        oauth_id=oauth_id
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, user_update: UserUpdate) -> Optional[User]:
    """
    Update user information.
    
    Args:
        db: Database session
        user_id: User ID
        user_update: User update data
        
    Returns:
        User: Updated user object, None if user not found
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        return None
    
    update_data = user_update.model_dump(exclude_unset=True)
    
    # Hash password if provided
    if "password" in update_data:
        from app.auth.password_utils import hash_password
        update_data["hashed_password"] = hash_password(update_data.pop("password"))
    
    for key, value in update_data.items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """
    Get multiple users with pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        
    Returns:
        List[User]: List of user objects
    """
    return db.query(User).offset(skip).limit(limit).all()

