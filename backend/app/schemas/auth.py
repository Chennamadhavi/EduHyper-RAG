"""
Pydantic validation schemas for authentication, user registration, and login.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for registering a new user."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique account username")
    email: str = Field(..., min_length=5, max_length=120, description="Valid user email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    role: Literal["teacher", "student"] = Field(..., description="Role: 'teacher' or 'student'")
    full_name: Optional[str] = Field(default=None, max_length=100, description="Optional display name")

    @field_validator("username")
    @classmethod
    def validate_username(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Username cannot be empty or whitespace only.")
        return cleaned

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "@" not in cleaned or "." not in cleaned:
            raise ValueError("Email format is invalid.")
        return cleaned


class UserLoginRequest(BaseModel):
    """Payload for user login via username or email."""
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Plain-text password")


class UserResponse(BaseModel):
    """Safe user profile response without password hashes."""
    id: int
    username: str
    email: str
    role: str
    created_at: Optional[str] = None


class TokenResponse(BaseModel):
    """JWT bearer token and authenticated user payload."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
