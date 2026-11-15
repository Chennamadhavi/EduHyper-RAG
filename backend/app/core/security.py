"""
Security and JWT token management for EduHyper-RAG.
Reuses existing PBKDF2 password hashing from src.auth.authenticator to preserve database compatibility.
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt

from backend.app.core.config import settings
from src.auth.authenticator import hash_password, verify_password


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Creates a signed JWT access token.
    
    Args:
        data: Dictionary of claims to include (e.g. sub, role, user_id).
        expires_delta: Optional custom duration.
        
    Returns:
        Encoded JWT token string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.jwt_access_token_expire_minutes)
        
    to_encode.update({
        "exp": expire,
        "iat": now,
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decodes and validates a JWT access token.
    
    Args:
        token: Encoded JWT string.
        
    Returns:
        Decoded payload dictionary, or None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except (jwt.ExpiredSignatureError, jwt.PyJWTError):
        return None


__all__ = [
    "create_access_token",
    "decode_access_token",
    "hash_password",
    "verify_password",
]
