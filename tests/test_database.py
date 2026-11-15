"""
Unit tests for Database Models & Data Access Layer.
"""

import pytest
from src.database.db import init_db
from src.database.models import (
    create_course,
    create_document,
    create_user,
    enroll_student_in_course,
    get_courses_by_teacher,
    get_documents_by_course,
    get_student_accessible_documents,
    get_student_qa_history,
    record_qa_history,
    update_document_status,
)


@pytest.fixture(autouse=True)
def setup_test_db(tmp_path, monkeypatch):
    test_db = tmp_path / "test_models.db"
    monkeypatch.setattr("src.config.config.db_path", test_db)
    init_db(test_db)


def test_course_and_document_crud():
    teacher = create_user("prof_smith", "smith@test.edu", "hash123", "teacher")
    course = create_course("CS101", "Intro to CS", "Basic programming", teacher["id"])
    assert course["course_code"] == "CS101"

    doc = create_document(
        doc_id="cs101_ch1",
        filename="ch1.pdf",
        file_path="/tmp/ch1.pdf",
        course_id=course["id"],
        uploaded_by=teacher["id"],
        status="PROCESSING",
    )
    assert doc["doc_id"] == "cs101_ch1"
    assert doc["status"] == "PROCESSING"

    update_document_status("cs101_ch1", status="READY", num_chunks=10, num_concepts=5, num_hyperedges=2)
    course_docs = get_documents_by_course(course["id"])
    assert len(course_docs) == 1
    assert course_docs[0]["status"] == "READY"
    assert course_docs[0]["num_chunks"] == 10


def test_enrollment_and_qa_history():
    teacher = create_user("prof_jones", "jones@test.edu", "hash123", "teacher")
    student = create_user("alice", "alice@test.edu", "hash123", "student")

    course = create_course("MATH101", "Calculus", "Derivatives & Integrals", teacher["id"])
    doc = create_document("calc_ch1", "calc.txt", "/tmp/calc.txt", course["id"], teacher["id"], "READY")

    enroll_student_in_course(course["id"], student["id"])
    acc_docs = get_student_accessible_documents(student["id"])
    assert len(acc_docs) == 1
    assert acc_docs[0]["doc_id"] == "calc_ch1"

    log_id = record_qa_history(
        student_id=student["id"],
        doc_id="calc_ch1",
        course_id=course["id"],
        user_query="What is a derivative?",
        generated_answer="A derivative represents a rate of change.",
        confidence_level="High",
        support_score=0.95,
        verification_decision="ACCEPT",
    )
    assert log_id > 0

    history = get_student_qa_history(student["id"])
    assert len(history) == 1
    assert history[0]["user_query"] == "What is a derivative?"
    assert history[0]["support_score"] == 0.95
