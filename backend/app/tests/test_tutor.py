"""
Integration and Unit Tests for AI Tutor API Router.
Validates sample question retrieval, personal QA history tracking,
document scope enforcement, and full online retrieval pipeline integration.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from src.database.db import init_db
from src.database.models import (
    create_course,
    create_document,
    create_user,
    record_qa_history,
)
from src.config import config


@pytest.fixture(autouse=True)
def setup_isolated_test_env(tmp_path, monkeypatch):
    """Isolate tests into a temporary directory and SQLite database."""
    test_db = tmp_path / "test_tutor_api.db"
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


def test_get_sample_questions(client):
    """GET /api/tutor/sample-questions returns sample educational questions."""
    res = client.get("/api/tutor/sample-questions")
    assert res.status_code == 200
    questions = res.json()
    assert isinstance(questions, list)
    assert len(questions) > 0
    assert any("Photosystem" in q or "Calvin" in q for q in questions)


def test_tutor_history_for_student(client):
    """GET /api/tutor/history returns student QA history with verification metadata."""
    # 1. Register teacher and course
    teacher = create_user("t_chem", "tchem@school.edu", "hash123", "teacher")
    course = create_course("CHEM101", "Chemistry I", "Introductory Chemistry", teacher["id"])

    # 2. Register student
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "student_tutor_test",
            "email": "student_test@school.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    assert reg_res.status_code == 201
    student_token = reg_res.json()["access_token"]
    student_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {student_token}"}

    # 3. History initially empty
    empty_res = client.get("/api/tutor/history", headers=headers)
    assert empty_res.status_code == 200
    assert empty_res.json() == []

    # 4. Insert mock QA history directly with valid course_id
    record_qa_history(
        student_id=student_id,
        doc_id="test_doc_001",
        course_id=course["id"],
        user_query="What is photosynthesis?",
        generated_answer="Photosynthesis converts light energy into chemical energy.",
        confidence_level="High",
        support_score=0.95,
        verification_decision="VERIFIED",
    )

    # 5. Fetch history
    history_res = client.get("/api/tutor/history", headers=headers)
    assert history_res.status_code == 200
    items = history_res.json()
    assert len(items) == 1
    assert items[0]["user_query"] == "What is photosynthesis?"
    assert items[0]["verification_decision"] == "VERIFIED"
    assert items[0]["support_score"] == 0.95
    assert items[0]["confidence_level"] == "High"


def test_tutor_query_missing_document(client):
    """POST /api/tutor/query returns 404 if document does not exist."""
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "student_query_404",
            "email": "query404@school.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    student_token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {student_token}"}

    payload = {
        "query": "How does photosynthesis work?",
        "doc_id": "non_existent_doc_id",
        "course_id": 1,
    }
    res = client.post("/api/tutor/query", json=payload, headers=headers)
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_tutor_query_pipeline_success(client, monkeypatch):
    """POST /api/tutor/query successfully runs multi-phase retrieval and returns verified response."""
    # 1. Setup teacher and course
    teacher = create_user("t_bio_prof", "prof_bio@school.edu", "hash123", "teacher")
    course = create_course("BIO101", "General Biology", "Cellular & Molecular Biology", teacher["id"])

    # 2. Register student
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "student_tutor_query",
            "email": "tutor_query@school.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    student_token = reg_res.json()["access_token"]
    student_id = reg_res.json()["user"]["id"]
    headers = {"Authorization": f"Bearer {student_token}"}

    # 3. Register a document in SQLite database
    create_document(
        doc_id="doc_bio_101",
        filename="bio101_chapter1.pdf",
        file_path="mock_path.pdf",
        course_id=course["id"],
        uploaded_by=teacher["id"],
        status="READY",
    )

    # 4. Mock the AI pipeline components
    mock_state = {
        "user_query": "What is the primary function of Photosystem II?",
        "retrieved_chunks": [
            {
                "chunk_id": "chunk_0",
                "content": "Photosystem II absorbs light and catalyzes the photolysis of water.",
                "score": 0.88,
                "source": "bio101_chapter1.pdf",
                "page": 2,
            }
        ],
        "retrieved_hyperedges": [{"edge_id": "edge_1", "concepts": ["Photosystem II", "Photolysis"]}],
        "retrieved_concepts": [{"name": "Photosystem II"}, {"name": "Photolysis"}],
        "verification_reasoning": "Sufficient evidence retrieved from textbook.",
    }

    monkeypatch.setattr(
        "backend.app.api.tutor.run_agentic_verification",
        lambda user_query, max_iterations, doc_id, course_id: mock_state,
    )

    class MockAnswerGen:
        def generate_answer(self, state):
            return {
                "answer": "Photosystem II catalyzes water oxidation to release oxygen and electrons.",
                "supporting_chunks": ["chunk_0"],
                "supporting_hyperedges": ["edge_1"],
            }

    monkeypatch.setattr("backend.app.api.tutor.EducationalAnswerGenerator", MockAnswerGen)

    class MockVerReport:
        support_score = 0.92
        decision = "VERIFIED"
        def model_dump(self):
            return {"decision": "VERIFIED", "support_score": 0.92}

    class MockChecker:
        def __init__(self, min_support_score=0.7):
            pass
        def verify_answer(self, **kwargs):
            return MockVerReport()

    monkeypatch.setattr("backend.app.api.tutor.HallucinationChecker", MockChecker)

    class MockExpReport:
        confidence_level = "High"
        def model_dump(self):
            return {"confidence_level": "High"}

    class MockExpEngine:
        def generate_explanation(self, state, answer, ver_report):
            return MockExpReport()

    monkeypatch.setattr("backend.app.api.tutor.EduExplainabilityEngine", MockExpEngine)

    # 5. Invoke endpoint
    payload = {
        "query": "What is the primary function of Photosystem II?",
        "doc_id": "doc_bio_101",
        "course_id": course["id"],
        "min_support_score": 0.7,
    }
    res = client.post("/api/tutor/query", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["answer"] == "Photosystem II catalyzes water oxidation to release oxygen and electrons."
    assert data["confidence_level"] == "High"
    assert data["verification_decision"] == "VERIFIED"
    assert data["support_score"] == 0.92
    assert len(data["retrieved_chunk_details"]) == 1
    assert data["retrieved_chunk_details"][0]["chunk_id"] == "chunk_0"
    assert "Photosystem II" in data["retrieved_concepts"]

    # 6. Verify interaction was stored in DB history
    history_res = client.get("/api/tutor/history", headers=headers)
    assert history_res.status_code == 200
    h_items = history_res.json()
    assert len(h_items) == 1
    assert h_items[0]["student_id"] == student_id
    assert h_items[0]["doc_id"] == "doc_bio_101"
    assert h_items[0]["verification_decision"] == "VERIFIED"
