"""
Authentication and Session State Management Engine for EduHyperRAG.

This module handles:
- User registration
- Password hashing and verification
- User authentication
- Session state management
- Login/logout
- Optional demo teacher/student accounts

IMPORTANT:
No subject, course, chapter, textbook, PDF, or document is
hard-coded in this module.

Courses and documents must be created dynamically through
the teacher dashboard.
"""

import hashlib
import secrets
from typing import Any, Dict, Optional

import streamlit as st

from src.database.db import init_db
from src.database.models import (
    create_user,
    get_user_by_username,
)
from src.utils.logger import get_logger


logger = get_logger("authenticator")


# ============================================================
# PASSWORD HASHING
# ============================================================

def hash_password(
    password: str,
    salt: Optional[bytes] = None,
) -> str:
    """
    Hash a password using PBKDF2-HMAC-SHA256.

    Args:
        password: Plain-text password.
        salt: Optional salt. A new random salt is generated
              when one is not supplied.

    Returns:
        A string containing:
        <salt_hex>$<hash_hex>
    """

    if not salt:
        salt = secrets.token_bytes(16)

    key = hashlib.pbkdf2_hmac(
        hash_name="sha256",
        password=password.encode("utf-8"),
        salt=salt,
        iterations=100000,
    )

    return f"{salt.hex()}${key.hex()}"


# ============================================================
# PASSWORD VERIFICATION
# ============================================================

def verify_password(
    password: str,
    stored_hash: str,
) -> bool:
    """
    Verify a password against a previously stored hash.

    Args:
        password: Password entered by the user.
        stored_hash: Stored PBKDF2 password hash.

    Returns:
        True if the password is correct, otherwise False.
    """

    try:
        salt_hex, hash_hex = stored_hash.split("$")

        salt = bytes.fromhex(salt_hex)

        recalculated = hash_password(
            password,
            salt=salt,
        )

        return secrets.compare_digest(
            recalculated,
            stored_hash,
        )

    except Exception as e:
        logger.error(
            f"Error verifying password: {str(e)}"
        )
        return False


# ============================================================
# USER REGISTRATION
# ============================================================

def register_user(
    username: str,
    email: str,
    password: str,
    role: str,
) -> Dict[str, Any]:
    """
    Register a new EduHyperRAG user.

    Supported roles:
        - teacher
        - student

    Args:
        username: Unique username.
        email: User email.
        password: Plain-text password.
        role: User role.

    Returns:
        Newly created user dictionary.

    Raises:
        ValueError: If role or password is invalid.
    """

    if role not in ("teacher", "student"):
        raise ValueError(
            "Invalid role. Role must be 'teacher' or 'student'."
        )

    if len(password) < 6:
        raise ValueError(
            "Password must be at least 6 characters long."
        )

    pwd_hash = hash_password(password)

    user = create_user(
        username=username,
        email=email,
        password_hash=pwd_hash,
        role=role,
    )

    logger.info(
        f"Registered new user '{username}' "
        f"with role '{role}'."
    )

    return user


# ============================================================
# USER AUTHENTICATION
# ============================================================

def authenticate_user(
    username: str,
    password: str,
) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user.

    Args:
        username: Username entered by the user.
        password: Password entered by the user.

    Returns:
        User dictionary if authentication succeeds,
        otherwise None.
    """

    user = get_user_by_username(username)

    if not user:
        return None

    if verify_password(
        password,
        user["password_hash"],
    ):
        return user

    return None


# ============================================================
# SESSION STATE
# ============================================================

def init_session_state() -> None:
    """
    Initialize Streamlit session state variables.
    """

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if "user_id" not in st.session_state:
        st.session_state["user_id"] = None

    if "username" not in st.session_state:
        st.session_state["username"] = ""

    if "user_role" not in st.session_state:
        st.session_state["user_role"] = ""


# ============================================================
# LOGIN
# ============================================================

def login_user(
    user: Dict[str, Any],
) -> None:
    """
    Store authenticated user information in Streamlit
    session state.
    """

    st.session_state["authenticated"] = True

    st.session_state["user_id"] = user["id"]

    st.session_state["username"] = user["username"]

    st.session_state["user_role"] = user["role"]

    logger.info(
        f"User '{user['username']}' "
        f"logged in as {user['role']}."
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_user() -> None:
    """
    Clear authenticated user information.
    """

    st.session_state["authenticated"] = False

    st.session_state["user_id"] = None

    st.session_state["username"] = ""

    st.session_state["user_role"] = ""

    logger.info("User logged out.")


# ============================================================
# OPTIONAL DEMO USERS
# ============================================================

def seed_demo_data() -> None:
    """
    Initialize the database and create optional demo accounts.

    IMPORTANT:
    This function intentionally DOES NOT create:

    - Any subject
    - Any course
    - Any chapter
    - Any textbook
    - Any PDF
    - Any document
    - Any knowledge-base data
    - Any hypergraph data
    - Any embeddings

    Teachers create courses and upload documents dynamically
    through the application.

    Demo accounts:

        Teacher
        Username: teacher
        Password: password123

        Student
        Username: student
        Password: password123
    """

    # --------------------------------------------------------
    # Initialize database
    # --------------------------------------------------------

    init_db()

    # --------------------------------------------------------
    # Create demo teacher account
    # --------------------------------------------------------

    teacher = get_user_by_username("teacher")

    if not teacher:
        try:
            register_user(
                username="teacher",
                email="teacher@eduhyperrag.edu",
                password="password123",
                role="teacher",
            )

            logger.info(
                "Demo teacher account created."
            )

        except Exception as e:
            logger.warning(
                f"Could not create demo teacher: {str(e)}"
            )

    # --------------------------------------------------------
    # Create demo student account
    # --------------------------------------------------------

    student = get_user_by_username("student")

    if not student:
        try:
            register_user(
                username="student",
                email="student@eduhyperrag.edu",
                password="password123",
                role="student",
            )

            logger.info(
                "Demo student account created."
            )

        except Exception as e:
            logger.warning(
                f"Could not create demo student: {str(e)}"
            )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # DO NOT create any course/document here.
    #
    # The system must remain completely subject-independent.
    #
    # Example:
    #
    # Teacher uploads:
    #   AI.pdf
    #
    # or:
    #   DBMS.pdf
    #
    # or:
    #   Physics.pdf
    #
    # or:
    #   Biology.pdf
    #
    # or any other educational PDF.
    #
    # The teacher dashboard should create the course/document
    # dynamically.
    # --------------------------------------------------------

    logger.info(
        "Demo authentication data initialized. "
        "No subject-specific course or document was created."
    )