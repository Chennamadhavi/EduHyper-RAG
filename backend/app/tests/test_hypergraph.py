"""
Unit and Integration Tests for Hypergraph Explorer API Router.
Validates concept nodes, high-order hyperedge relationships,
cardinality metrics, and concept inspection.
"""

import json
import pytest
from fastapi.testclient import TestClient

from backend.app.main import create_app
from src.database.db import init_db
from src.database.models import create_course, create_document, create_user
from src.config import config


@pytest.fixture(autouse=True)
def setup_isolated_test_env(tmp_path, monkeypatch):
    """Isolate tests into a temporary directory and SQLite database."""
    test_db = tmp_path / "test_hypergraph_api.db"
    kb_dir = tmp_path / "data" / "knowledge_base"
    kb_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(config, "db_path", test_db)
    monkeypatch.setattr(config, "data_dir", tmp_path / "data")
    monkeypatch.setattr(config, "raw_data_dir", tmp_path / "data" / "raw")
    monkeypatch.setattr(config, "processed_data_dir", tmp_path / "data" / "processed")
    monkeypatch.setattr(config, "chunks_data_dir", tmp_path / "data" / "chunks")
    monkeypatch.setattr(config, "knowledge_base_dir", kb_dir)
    monkeypatch.setattr(config, "courses_data_dir", tmp_path / "data" / "courses")
    init_db(test_db)


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_get_hypergraph_missing_document(client):
    """GET /api/hypergraph/documents/{doc_id} returns 404 if document does not exist."""
    res = client.post(
        "/api/auth/register",
        json={
            "username": "h_student_1",
            "email": "h1@school.edu",
            "password": "Password123!",
            "role": "student",
        },
    )
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    get_res = client.get("/api/hypergraph/documents/unknown_doc_xyz", headers=headers)
    assert get_res.status_code == 404


def test_get_hypergraph_success(client, tmp_path):
    """GET /api/hypergraph/documents/{doc_id} returns graph nodes, high-order hyperedges, and metrics."""
    # 1. Register teacher and course
    teacher = create_user("h_prof", "prof_h@school.edu", "pass123", "teacher")
    course = create_course("AI201", "Artificial Intelligence", "Advanced AI", teacher["id"])

    # 2. Register document
    doc_id = "test_ai_doc"
    create_document(
        doc_id=doc_id,
        filename="ai_lecture.pdf",
        file_path="mock.pdf",
        course_id=course["id"],
        uploaded_by=teacher["id"],
        status="READY",
    )

    # 3. Create mock hypergraph JSON
    kb_dir = config.knowledge_base_dir
    h_data = {
        "metadata": {
            "num_nodes": 3,
            "num_hyperedges": 2,
            "largest_hyperedge_id": "hyp_high_order_01",
            "largest_hyperedge_size": 3,
        },
        "concepts": {
            "Neural Networks": {
                "concept_id": "Neural Networks",
                "name": "Neural Networks",
                "entity_type": "Architecture",
                "description": "Computational graph inspired by biological neurons.",
                "source_chunk_ids": ["chk_01"],
            },
            "Backpropagation": {
                "concept_id": "Backpropagation",
                "name": "Backpropagation",
                "entity_type": "Algorithm",
                "description": "Reverse-mode automatic differentiation algorithm.",
                "source_chunk_ids": ["chk_01", "chk_02"],
            },
            "Gradient Descent": {
                "concept_id": "Gradient Descent",
                "name": "Gradient Descent",
                "entity_type": "Optimization",
                "description": "First-order iterative optimization algorithm.",
                "source_chunk_ids": ["chk_02"],
            },
        },
        "hyperedges": {
            "hyp_high_order_01": {
                "hyperedge_id": "hyp_high_order_01",
                "label": "learning_triad",
                "concepts": ["Neural Networks", "Backpropagation", "Gradient Descent"],
                "description": "Neural Networks use Backpropagation and Gradient Descent to learn weights.",
                "source_chunk_ids": ["chk_01"],
            },
            "hyp_pairwise_02": {
                "hyperedge_id": "hyp_pairwise_02",
                "label": "optimizes",
                "concepts": ["Backpropagation", "Gradient Descent"],
                "description": "Backpropagation calculates gradients for Gradient Descent.",
                "source_chunk_ids": ["chk_02"],
            },
        },
    }

    h_path = kb_dir / f"hypergraph_{doc_id}.json"
    h_path.write_text(json.dumps(h_data), encoding="utf-8")

    # 4. Request hypergraph
    login_res = client.post(
        "/api/auth/login",
        json={"username": "h_prof", "password": "Password123!"},
    )
    # Register an account to get a valid token
    reg_res = client.post(
        "/api/auth/register",
        json={
            "username": "h_viewer",
            "email": "h_viewer@school.edu",
            "password": "Password123!",
            "role": "teacher",
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get(f"/api/hypergraph/documents/{doc_id}", headers=headers)
    assert res.status_code == 200
    data = res.json()

    assert data["doc_id"] == doc_id
    assert data["filename"] == "ai_lecture.pdf"
    assert data["metadata"]["num_nodes"] == 3
    assert data["metadata"]["num_hyperedges"] == 2
    assert data["metadata"]["num_high_order"] == 1  # 3 concepts >= 3
    assert data["metadata"]["num_pairwise"] == 1    # 2 concepts == 2
    assert data["metadata"]["largest_hyperedge_size"] == 3

    # Check node degree calculation
    nodes = {n["id"]: n for n in data["nodes"]}
    assert nodes["Neural Networks"]["degree"] == 1
    assert nodes["Backpropagation"]["degree"] == 2
    assert nodes["Gradient Descent"]["degree"] == 2

    # Check hyperedges
    edges = {e["hyperedge_id"]: e for e in data["hyperedges"]}
    assert edges["hyp_high_order_01"]["is_high_order"] is True
    assert edges["hyp_pairwise_02"]["is_high_order"] is False


def test_get_concept_details(client):
    """GET /api/hypergraph/documents/{doc_id}/concepts/{concept_name} returns concept inspection."""
    # 1. Setup doc and hypergraph
    teacher = create_user("t_chem_h", "chemh@school.edu", "pass123", "teacher")
    course = create_course("CHEM201", "Physical Chem", "Thermo", teacher["id"])
    doc_id = "doc_thermo"
    create_document(
        doc_id=doc_id,
        filename="thermo.pdf",
        file_path="mock.pdf",
        course_id=course["id"],
        uploaded_by=teacher["id"],
        status="READY",
    )

    h_data = {
        "metadata": {"num_nodes": 2, "num_hyperedges": 1, "largest_hyperedge_id": "e1", "largest_hyperedge_size": 2},
        "concepts": {
            "Entropy": {
                "name": "Entropy",
                "entity_type": "State Function",
                "description": "Measure of molecular disorder.",
                "source_chunk_ids": ["c1"],
            },
            "Enthalpy": {
                "name": "Enthalpy",
                "entity_type": "State Function",
                "description": "Total heat content.",
                "source_chunk_ids": ["c1"],
            },
        },
        "hyperedges": {
            "e1": {
                "hyperedge_id": "e1",
                "label": "thermo_potentials",
                "concepts": ["Entropy", "Enthalpy"],
                "description": "Relate through Gibbs Free Energy.",
                "source_chunk_ids": ["c1"],
            }
        },
    }
    (config.knowledge_base_dir / f"hypergraph_{doc_id}.json").write_text(json.dumps(h_data), encoding="utf-8")

    # 2. Register viewer
    reg = client.post(
        "/api/auth/register",
        json={"username": "viewer_user", "email": "viewer@school.edu", "password": "Password123!", "role": "teacher"},
    )
    headers = {"Authorization": f"Bearer {reg.json()['access_token']}"}

    # 3. Fetch concept
    res = client.get(f"/api/hypergraph/documents/{doc_id}/concepts/Entropy", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["concept"]["name"] == "Entropy"
    assert data["concept"]["entity_type"] == "State Function"
    assert len(data["connected_hyperedges"]) == 1
    assert data["connected_hyperedges"][0]["hyperedge_id"] == "e1"
    assert "Enthalpy" in data["neighbors"]

    # 4. Non-existent concept
    res_404 = client.get(f"/api/hypergraph/documents/{doc_id}/concepts/NonExistent", headers=headers)
    assert res_404.status_code == 404
