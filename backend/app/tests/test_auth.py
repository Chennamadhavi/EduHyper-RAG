"""
Unit & Integration tests for FastAPI Authentication & RBAC endpoints.
Validates registration, login, JWT token decoding, /me profile, and role enforcement.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from src.database.db import init_db
from src.config import config


@pytest.fixture(autouse=True)
def setup_isolated_test_db(tmp_path, monkeypatch):
    """Isolate tests into a temporary SQLite database to protect production/dev data."""
    test_db = tmp_path / "test_api_auth.db"
    monkeypatch.setattr(config, "db_path", test_db)
    init_db(test_db)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_register_teacher_success(client):
    payload = {
        "username": "prof_oak",
        "email": "oak@pokemon.edu",
        "password": "Password123!",
        "role": "teacher",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "prof_oak"
    assert data["user"]["role"] == "teacher"
    assert "password_hash" not in data["user"]


def test_register_student_success(client):
    payload = {
        "username": "ash_ketchum",
        "email": "ash@pallet.edu",
        "password": "GottaCatchEmAll123",
        "role": "student",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["role"] == "student"


def test_register_duplicate_username_fails(client):
    payload = {
        "username": "duplicate_user",
        "email": "first@edu.com",
        "password": "ValidPassword123",
        "role": "student",
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    payload2 = {
        "username": "duplicate_user",
        "email": "second@edu.com",
        "password": "ValidPassword123",
        "role": "student",
    }
    res2 = client.post("/api/auth/register", json=payload2)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"].lower()


def test_register_short_password_fails(client):
    payload = {
        "username": "short_pass_user",
        "email": "short@edu.com",
        "password": "123",
        "role": "student",
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422  # Pydantic validation fails min_length=6


def test_login_with_username_and_email(client):
    reg_payload = {
        "username": "dual_login_user",
        "email": "dual@university.edu",
        "password": "SecurePassword123",
        "role": "student",
    }
    client.post("/api/auth/register", json=reg_payload)

    # Login with username
    login_user_res = client.post(
        "/api/auth/login",
        json={"username": "dual_login_user", "password": "SecurePassword123"},
    )
    assert login_user_res.status_code == 200
    assert "access_token" in login_user_res.json()

    # Login with email
    login_email_res = client.post(
        "/api/auth/login",
        json={"username": "dual@university.edu", "password": "SecurePassword123"},
    )
    assert login_email_res.status_code == 200
    assert "access_token" in login_email_res.json()


def test_login_invalid_password_returns_401(client):
    reg_payload = {
        "username": "wrong_pwd_user",
        "email": "pwd@test.edu",
        "password": "CorrectPassword123",
        "role": "teacher",
    }
    client.post("/api/auth/register", json=reg_payload)

    login_res = client.post(
        "/api/auth/login",
        json={"username": "wrong_pwd_user", "password": "WrongPassword!"},
    )
    assert login_res.status_code == 401
    assert "Incorrect username or password" in login_res.json()["detail"]


def test_get_me_requires_token(client):
    res = client.get("/api/auth/me")
    assert res.status_code == 401


def test_get_me_with_valid_token(client):
    reg_payload = {
        "username": "me_user",
        "email": "me@test.edu",
        "password": "Password123",
        "role": "student",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    token = reg_res.json()["access_token"]

    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "me_user"
    assert data["email"] == "me@test.edu"
    assert data["role"] == "student"


def test_role_based_access_control(client):
    # Register teacher
    t_res = client.post(
        "/api/auth/register",
        json={
            "username": "real_teacher",
            "email": "t@school.edu",
            "password": "Pass123456",
            "role": "teacher",
        },
    )
    t_token = t_res.json()["access_token"]

    # Register student
    s_res = client.post(
        "/api/auth/register",
        json={
            "username": "real_student",
            "email": "s@school.edu",
            "password": "Pass123456",
            "role": "student",
        },
    )
    s_token = s_res.json()["access_token"]

    # Teacher accesses teacher route -> 200
    res_t_t = client.get("/api/auth/teacher-only", headers={"Authorization": f"Bearer {t_token}"})
    assert res_t_t.status_code == 200

    # Student accesses teacher route -> 403 Forbidden
    res_s_t = client.get("/api/auth/teacher-only", headers={"Authorization": f"Bearer {s_token}"})
    assert res_s_t.status_code == 403
    assert "Access forbidden" in res_s_t.json()["detail"]

    # Student accesses student route -> 200
    res_s_s = client.get("/api/auth/student-only", headers={"Authorization": f"Bearer {s_token}"})
    assert res_s_s.status_code == 200

    # Teacher accesses student route -> 403 Forbidden
    res_t_s = client.get("/api/auth/student-only", headers={"Authorization": f"Bearer {t_token}"})
    assert res_t_s.status_code == 403
