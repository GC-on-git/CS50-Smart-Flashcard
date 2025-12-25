"""
Security utilities
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Optional[dict]:
    """Decode and verify a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token has expired
        logger.warning("JWT token has expired")
        return None
    except jwt.JWTClaimsError as e:
        # Invalid token claims (e.g., expired, wrong audience)
        logger.warning(f"JWT claims validation failed: {e}")
        return None
    except jwt.InvalidSignatureError:
        # Token signature is invalid (wrong SECRET_KEY)
        logger.warning("JWT token signature is invalid - possible SECRET_KEY mismatch")
        return None
    except jwt.InvalidTokenError as e:
        # Invalid token format or other token errors
        logger.warning(f"JWT token is invalid: {e}")
        return None
    except JWTError as e:
        # Catch any other JWT-related errors
        logger.warning(f"JWT error: {e}")
        return None

