"""
Unit tests for Authentication & Password Hashing Module.
"""

import pytest
from src.auth.authenticator import (
    authenticate_user,
    hash_password,
    register_user,
    verify_password,
)
from src.database.db import init_db
from src.database.models import get_user_by_username


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_auth.db"
    monkeypatch.setattr("src.config.config.db_path", test_db)
    init_db(test_db)


def test_password_hashing():
    pwd = "SecretPassword123"
    hashed = hash_password(pwd)
    assert "$" in hashed
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_user_registration_and_authentication():
    user = register_user("testteacher", "teacher@test.com", "pass123", "teacher")
    assert user["username"] == "testteacher"
    assert user["role"] == "teacher"

    # Authenticate valid user
    auth_user = authenticate_user("testteacher", "pass123")
    assert auth_user is not None
    assert auth_user["id"] == user["id"]

    # Authenticate invalid password
    invalid_auth = authenticate_user("testteacher", "wrongpass")
    assert invalid_auth is None


def test_duplicate_user_registration_fails():
    register_user("uniqueuser", "user1@test.com", "pass123", "student")
    with pytest.raises(ValueError):
        register_user("uniqueuser", "user2@test.com", "pass123", "student")
