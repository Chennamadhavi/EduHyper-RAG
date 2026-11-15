"""
Integration & Unit tests for Course Management and Document Ingestion API endpoints.
Validates course creation, student enrollment, PDF/text document upload,
and automatic invocation of Phase 1-4 pipelines.
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from src.database.db import init_db
from src.config import config


@pytest.fixture(autouse=True)
def setup_isolated_test_env(tmp_path, monkeypatch):
    """Isolate tests into a temporary directory and SQLite database."""
    test_db = tmp_path / "test_courses_api.db"
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


def test_course_creation_and_listing(client):
    # 1. Register teacher
    teacher_res = client.post(
        "/api/auth/register",
        json={
            "username": "instructor_chem",
            "email": "chem@university.edu",
            "password": "Password123!",
            "role": "teacher",
        },
    )
    assert teacher_res.status_code == 201
    teacher_token = teacher_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {teacher_token}"}

    # 2. Create course
    course_payload = {
        "course_code": "CHEM101",
        "title": "General Chemistry I",
        "description": "Atomic structures, chemical bonding, and molecular interactions.",
    }
    create_res = client.post("/api/courses", json=course_payload, headers=headers)
    assert create_res.status_code == 201
    course_data = create_res.json()
    assert course_data["course_code"] == "CHEM101"
    assert course_data["title"] == "General Chemistry I"
    course_id = course_data["id"]

    # 3. List courses as teacher
    list_res = client.get("/api/courses", headers=headers)
    assert list_res.status_code == 200
    courses = list_res.json()
    assert len(courses) == 1
    assert courses[0]["id"] == course_id


def test_student_enrollment(client):
    # 1. Register teacher and create course
    t_res = client.post(
        "/api/auth/register",
        json={
            "username": "t_bio",
            "email": "tbio@school.edu",
            "password": "Password123!",
            "role": "teacher",
        },
    )
    t_token = t_res.json()["access_token"]
    c_res = client.post(
        "/api/courses",
        json={"course_code": "BIO201", "title": "Cellular Biology", "description": "Cell anatomy"},
        headers={"Authorization": f"Bearer {t_token}"},
    )
    course_id = c_res.json()["id"]

    # 2. Register student
    s_res = client.post(
        "/api/auth/register",
        json={
            "username": "s_learner",
            "email": "slearner@school.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    s_token = s_res.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    # 3. Student enrolls
    enroll_res = client.post(f"/api/courses/{course_id}/enroll", headers=s_headers)
    assert enroll_res.status_code == 200
    assert enroll_res.json()["success"] is True

    # 4. Student sees course in their enrolled list
    my_courses_res = client.get("/api/courses", headers=s_headers)
    assert my_courses_res.status_code == 200
    my_courses = my_courses_res.json()
    assert len(my_courses) == 1
    assert my_courses[0]["id"] == course_id
    assert my_courses[0]["is_enrolled"] is True


def test_dynamic_document_upload_and_pipeline_execution(client):
    # 1. Register teacher and create course
    t_res = client.post(
        "/api/auth/register",
        json={
            "username": "t_physics",
            "email": "tphys@school.edu",
            "password": "Password123!",
            "role": "teacher",
        },
    )
    t_token = t_res.json()["access_token"]
    t_headers = {"Authorization": f"Bearer {t_token}"}

    c_res = client.post(
        "/api/courses",
        json={"course_code": "PHYS101", "title": "Classical Mechanics", "description": "Newtonian physics"},
        headers=t_headers,
    )
    course_id = c_res.json()["id"]

    # 2. Upload document bytes to trigger dynamic ingestion
    sample_text = (
        "Newton's laws of motion are three basic laws of classical mechanics. "
        "The first law states that a body remains at rest unless acted upon by a net external force. "
        "The second law states that force equals the time derivative of momentum, or mass times acceleration (F = ma). "
        "The third law states that when one body exerts a force on a second body, the second body exerts a force equal in magnitude and opposite in direction."
    )
    file_bytes = io.BytesIO(sample_text.encode("utf-8"))

    upload_res = client.post(
        f"/api/documents/upload?course_id={course_id}",
        files={"file": ("newton_laws.txt", file_bytes, "text/plain")},
        headers=t_headers,
    )
    assert upload_res.status_code == 201
    data = upload_res.json()
    assert data["status"] == "READY"
    assert data["num_chunks"] > 0
    assert data["filename"] == "newton_laws.txt"

    # 3. List documents as teacher
    docs_res = client.get(f"/api/documents?course_id={course_id}", headers=t_headers)
    assert docs_res.status_code == 200
    docs = docs_res.json()
    assert len(docs) == 1
    assert docs[0]["filename"] == "newton_laws.txt"
    assert docs[0]["status"] == "READY"


def test_student_cannot_upload_document(client):
    # Register student
    s_res = client.post(
        "/api/auth/register",
        json={
            "username": "s_denied",
            "email": "denied@school.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    s_token = s_res.json()["access_token"]
    s_headers = {"Authorization": f"Bearer {s_token}"}

    file_bytes = io.BytesIO(b"Fake content")
    upload_res = client.post(
        "/api/documents/upload?course_id=1",
        files={"file": ("fake.txt", file_bytes, "text/plain")},
        headers=s_headers,
    )
    assert upload_res.status_code == 403
    assert "Access forbidden" in upload_res.json()["detail"]
