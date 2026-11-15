"""
Authentication router providing user registration, login, and profile verification.
"""

from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.core.security import create_access_token, verify_password
from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.api.deps import (
    get_current_user,
    get_current_teacher,
    get_current_student,
)
from src.auth.authenticator import register_user
from src.database.models import get_user_by_username
from src.database.db import get_db_connection


router = APIRouter()


def find_user_by_username_or_email(identifier: str) -> Dict[str, Any] | None:
    """Helper to locate a user by either username or lowercase email."""
    cleaned = identifier.strip()
    user = get_user_by_username(cleaned)
    if user:
        return user

    # Lookup by email
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE LOWER(email) = LOWER(?)", (cleaned,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student or teacher account",
)
async def register(payload: UserRegisterRequest):
    """
    Registers a new user into the database and returns a signed JWT access token.
    """
    try:
        user = register_user(
            username=payload.username,
            email=payload.email,
            password=payload.password,
            role=payload.role,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Issue JWT token
    token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["id"],
            "role": user["role"],
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            created_at=str(user.get("created_at", "")),
        ),
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate with username/email and password",
)
async def login(payload: UserLoginRequest):
    """
    Verifies user credentials and returns a JWT access token.
    """
    user = find_user_by_username_or_email(payload.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["id"],
            "role": user["role"],
        }
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(
            id=user["id"],
            username=user["username"],
            email=user["email"],
            role=user["role"],
            created_at=str(user.get("created_at", "")),
        ),
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current authenticated user profile",
)
async def get_me(current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Returns profile information for the authenticated bearer token holder.
    """
    return UserResponse(
        id=current_user["id"],
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"],
        created_at=str(current_user.get("created_at", "")),
    )


@router.get(
    "/teacher-only",
    summary="Verify teacher RBAC authorization",
)
async def verify_teacher_access(teacher: Dict[str, Any] = Depends(get_current_teacher)):
    """Protected endpoint verifying teacher-role authorization."""
    return {
        "status": "authorized",
        "message": f"Welcome instructor {teacher['username']}. Teacher permissions verified.",
        "role": teacher["role"],
    }


@router.get(
    "/student-only",
    summary="Verify student RBAC authorization",
)
async def verify_student_access(student: Dict[str, Any] = Depends(get_current_student)):
    """Protected endpoint verifying student-role authorization."""
    return {
        "status": "authorized",
        "message": f"Welcome learner {student['username']}. Student permissions verified.",
        "role": student["role"],
    }
