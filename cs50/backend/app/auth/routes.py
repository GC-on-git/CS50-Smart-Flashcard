"""
Authentication routes
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.user import UserCreate, UserResponse, Token, LoginRequest
from app.services.crud_users import create_user, get_user_by_email
from app.auth.password_utils import hash_password, verify_user_password
from app.auth.jwt_handler import create_token_pair, refresh_access_token
from app.core.dependencies import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    Creates a new user account with email, username, and password.
    Returns the created user information.
    
    Args:
        user_data: User registration data (email, username, password)
        db: Database session
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if user already exists
    db_user = get_user_by_email(db, email=user_data.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    from app.services.crud_users import get_user_by_username
    db_user = get_user_by_username(db, username=user_data.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    new_user = create_user(
        db=db,
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password
    )
    
    return new_user

@router.post("/login", response_model=Token)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.
    
    Authenticates user with email and password.
    Returns access and refresh tokens for subsequent API calls.
    
    Args:
        login_data: Login credentials (email, password)
        db: Database session
        
    Returns:
        Token: Access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    user = get_user_by_email(db, email=login_data.email)
    if not user or not verify_user_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Create token pair
    tokens = create_token_pair(user.id)
    
    return Token(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type="bearer"
    )

@router.get("/profile", response_model=UserResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile.
    
    Returns the profile information of the currently authenticated user.
    Requires a valid JWT access token.
    
    Args:
        current_user: Current authenticated user from dependency
        
    Returns:
        UserResponse: Current user information
    """
    return current_user

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token.
    
    Generates a new access token using a valid refresh token.
    
    Args:
        refresh_token: Valid refresh token
        db: Database session
        
    Returns:
        Token: New access token and same refresh token
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    new_access_token = refresh_access_token(refresh_token)
    if new_access_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Decode refresh token to get user_id for returning refresh token
    from .jwt_handler import verify_token
    payload = verify_token(refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    return Token(
        access_token=new_access_token,
        refresh_token=refresh_token,
        token_type="bearer"
    )

