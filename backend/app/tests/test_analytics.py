"""
Unit and Integration Tests for Analytics and Student Progress API Router.
Validates teacher classroom monitoring, hallucination auditing, student learning progress,
role-based permissions, and Phase 9 benchmark endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from src.database.db import init_db
from src.database.models import (
    create_course,
    create_document,
    create_user,
    enroll_student_in_course,
    record_qa_history,
)
from src.config import config


@pytest.fixture(autouse=True)
def setup_isolated_test_env(tmp_path, monkeypatch):
    """Isolate tests into a temporary directory and SQLite database."""
    test_db = tmp_path / "test_analytics_api.db"
    monkeypatch.setattr(config, "db_path", test_db)
    monkeypatch.setattr(config, "data_dir", tmp_path / "data")
    monkeypatch.setattr(config, "raw_data_dir", tmp_path / "data" / "raw")
    monkeypatch.setattr(config, "processed_data_dir", tmp_path / "data" / "processed")
    monkeypatch.setattr(config, "chunks_data_dir", tmp_path / "data" / "chunks")
    monkeypatch.setattr(config, "knowledge_base_dir", tmp_path / "data" / "knowledge_base")
    monkeypatch.setattr(config, "courses_data_dir", tmp_path / "data" / "courses")
    init_db(test_db)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_teacher_analytics_endpoint(client):
    """GET /api/analytics/teacher returns classroom metrics, course breakdown, and flagged queries."""
    # 1. Register teacher and create course
    teacher_res = client.post(
        "/api/auth/register",
        json={
            "username": "prof_analytics",
            "email": "prof_a@school.edu",
            "password": "Password123!",
            "role": "teacher",
        },
    )
    assert teacher_res.status_code == 201
    teacher_token = teacher_res.json()["access_token"]
    teacher_id = teacher_res.json()["user"]["id"]
    t_headers = {"Authorization": f"Bearer {teacher_token}"}

    course = create_course("DATA301", "Data Engineering", "Big data", teacher_id)
    doc = create_document("doc_data_1", "notes.pdf", "path.pdf", course["id"], teacher_id, "READY")

    # 2. Register student and enroll
    student = create_user("student_a", "student_a@school.edu", "pass123", "student")
    enroll_student_in_course(course["id"], student["id"])

    # 3. Add 2 QA history items (one verified, one flagged)
    record_qa_history(
        student_id=student["id"],
        doc_id=doc["doc_id"],
        course_id=course["id"],
        user_query="What is MapReduce?",
        generated_answer="MapReduce is a distributed programming model.",
        confidence_level="HIGH",
        support_score=0.95,
        verification_decision="VERIFIED",
    )
    record_qa_history(
        student_id=student["id"],
        doc_id=doc["doc_id"],
        course_id=course["id"],
        user_query="How does quantum teleportation work?",
        generated_answer="Quantum teleportation transfers states.",
        confidence_level="LOW",
        support_score=0.30,
        verification_decision="REGENERATE",
    )

    # 4. Fetch teacher analytics
    res = client.get("/api/analytics/teacher", headers=t_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["total_courses"] == 1
    assert data["total_documents"] == 1
    assert data["total_queries"] == 2
    assert data["flagged_queries"] == 1
    assert data["hallucination_rate_pct"] == 50.0
    assert data["avg_support_score"] == pytest.approx(0.625, 0.01)

    # Check breakdowns
    assert data["decisions_breakdown"].get("VERIFIED") == 1
    assert data["decisions_breakdown"].get("REGENERATE") == 1
    assert len(data["courses_breakdown"]) == 1
    assert data["courses_breakdown"][0]["enrolled_count"] == 1
    assert data["courses_breakdown"][0]["total_queries"] == 2

    # Check recent and flagged lists
    assert len(data["recent_questions"]) == 2
    assert len(data["flagged_questions"]) == 1
    assert data["flagged_questions"][0]["user_query"] == "How does quantum teleportation work?"


def test_student_progress_endpoint(client):
    """GET /api/analytics/student returns personal learning analytics and grounding progress."""
    # 1. Setup teacher and course
    teacher = create_user("t_phys", "phys@school.edu", "pass123", "teacher")
    course = create_course("PHYS202", "Electromagnetism", "Maxwell equations", teacher["id"])
    doc = create_document("doc_phys_1", "maxwell.pdf", "path.pdf", course["id"], teacher["id"], "READY")

    # 2. Register student and enroll
    student_res = client.post(
        "/api/auth/register",
        json={
            "username": "student_progress_test",
            "email": "prog_test@school.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert student_res.status_code == 201
    student_token = student_res.json()["access_token"]
    student_id = student_res.json()["user"]["id"]
    s_headers = {"Authorization": f"Bearer {student_token}"}

    enroll_student_in_course(course["id"], student_id)

    # 3. Add verified QA interaction
    record_qa_history(
        student_id=student_id,
        doc_id=doc["doc_id"],
        course_id=course["id"],
        user_query="What is Faraday's law of induction?",
        generated_answer="A changing magnetic field induces an electromotive force.",
        confidence_level="HIGH",
        support_score=0.98,
        verification_decision="VERIFIED",
    )

    # 4. Fetch student progress
    res = client.get("/api/analytics/student", headers=s_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["student_id"] == student_id
    assert data["student_name"] == "student_progress_test"
    assert data["total_queries"] == 1
    assert data["enrolled_courses_count"] == 1
    assert data["avg_support_score"] == 0.98
    assert data["verified_rate_pct"] == 100.0
    assert len(data["course_progress"]) == 1
    assert data["course_progress"][0]["course_code"] == "PHYS202"
    assert len(data["recent_activity"]) == 1


def test_role_based_access_control_analytics(client):
    """Verifies that students cannot access teacher analytics and vice versa."""
    # Register teacher
    t_res = client.post(
        "/api/auth/register",
        json={"username": "t_rbac", "email": "trbac@school.edu", "password": "Password123!", "role": "teacher"},
    )
    t_token = t_res.json()["access_token"]

    # Register student
    s_res = client.post(
        "/api/auth/register",
        json={"username": "s_rbac", "email": "srbac@school.edu", "password": "Password123!", "role": "student"},
    )
    s_token = s_res.json()["access_token"]

    # Student calling teacher analytics -> 403 Forbidden
    res_s = client.get("/api/analytics/teacher", headers={"Authorization": f"Bearer {s_token}"})
    assert res_s.status_code == 403

    # Teacher calling student progress -> 403 Forbidden
    res_t = client.get("/api/analytics/student", headers={"Authorization": f"Bearer {t_token}"})
    assert res_t.status_code == 403


def test_benchmark_endpoint(client):
    """GET /api/analytics/benchmark returns Phase 9 empirical comparison results."""
    reg = client.post(
        "/api/auth/register",
        json={"username": "viewer_bm", "email": "vbm@school.edu", "password": "Password123!", "role": "student"},
    )
    token = reg.json()["access_token"]

    res = client.get("/api/analytics/benchmark", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()

    assert "rows" in data
    assert len(data["rows"]) == 6
    architectures = [r["architecture"] for r in data["rows"]]
    assert "Proposed Enhanced Hyper-RAG" in architectures
    assert "Vanilla LLM" in architectures
    assert "Traditional RAG" in architectures
