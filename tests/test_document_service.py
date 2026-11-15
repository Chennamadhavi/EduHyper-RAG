"""
Integration unit tests for DocumentProcessingService.
Tests dynamic PDF/text document ingestion reusing Phase 1-3 components.
"""

import pytest
from src.auth.authenticator import register_user
from src.database.db import init_db
from src.database.models import create_course, get_document_by_doc_id
from src.services.document_service import DocumentProcessingService


@pytest.fixture(autouse=True)
def setup_test_env(tmp_path, monkeypatch):
    test_db = tmp_path / "test_service.db"
    monkeypatch.setattr("src.config.config.db_path", test_db)
    monkeypatch.setattr("src.config.config.data_dir", tmp_path / "data")
    monkeypatch.setattr("src.config.config.raw_data_dir", tmp_path / "data" / "raw")
    monkeypatch.setattr("src.config.config.processed_data_dir", tmp_path / "data" / "processed")
    monkeypatch.setattr("src.config.config.chunks_data_dir", tmp_path / "data" / "chunks")
    monkeypatch.setattr("src.config.config.knowledge_base_dir", tmp_path / "data" / "knowledge_base")
    monkeypatch.setattr("src.config.config.courses_data_dir", tmp_path / "data" / "courses")
    init_db(test_db)


def test_dynamic_document_processing_service():
    teacher = register_user("service_teacher", "service@test.com", "pass123", "teacher")
    course = create_course("PHY101", "Physics Basics", "Mechanics", teacher["id"])

    file_content = (
        "Photosynthesis is a biological process used by plants to convert light energy into chemical energy. "
        "Chlorophyll absorbs photons in the thylakoid membrane. Photosystem II splits water into hydrogen and oxygen gas. "
        "The Calvin cycle utilizes ATP and NADPH synthesized in light-dependent reactions to fix carbon dioxide."
    )
    file_bytes = file_content.encode("utf-8")

    service = DocumentProcessingService()
    summary = service.process_uploaded_file(
        file_name="physics_ch1.txt",
        file_bytes=file_bytes,
        course_id=course["id"],
        uploaded_by=teacher["id"],
        custom_doc_id="physics_ch1",
    )

    assert summary["doc_id"] == "physics_ch1"
    assert summary["status"] == "READY"
    assert summary["num_chunks"] > 0

    doc_rec = get_document_by_doc_id("physics_ch1")
    assert doc_rec is not None
    assert doc_rec["status"] == "READY"
    assert doc_rec["num_chunks"] == summary["num_chunks"]
