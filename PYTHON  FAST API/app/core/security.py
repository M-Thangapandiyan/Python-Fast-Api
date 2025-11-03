"""
Security utilities for authentication and password handling.
"""
import jwt
import bcrypt
from datetime import timedelta, datetime, timezone
from app.core.config import settings
from app.core.exceptions import InvalidTokenError
from app.utils.logger import logger


def create_access_token(data: dict) -> str:
    """
    Create a JWT access token.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire, "type": "access"})
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.info("Access token created successfully")
    return token


def create_refresh_token(data: dict) -> str:
    """
    Create a JWT refresh token.
    """
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.REFRESH_TOKEN_EXPIRE_HOURS)
    payload.update({"exp": expire, "type": "refresh"})
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    logger.info("Refresh token created successfully")
    return token


def verify_token(token: str, expected_type: str = "access") -> dict:
    """
    Verify and decode a JWT token.
    """
    try:
        decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        logger.info("Token verified successfully")
        if decoded_token.get("type") != expected_type:
            raise InvalidTokenError(f"Invalid token type. Expected: {expected_type}")
        return decoded_token
    except jwt.InvalidTokenError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    salt = bcrypt.gensalt()
    logger.info(f" salt :  {salt}")
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    logger.info(f" hashed :  {hashed}")
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.info(f"Password verification error: {e}")
        return False

