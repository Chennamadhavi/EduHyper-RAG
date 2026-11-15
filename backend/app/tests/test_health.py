"""
Automated Test Suite for FastAPI Backend Foundation and Health Checks.
Covers:
1. Health endpoint returns HTTP 200.
2. Expected JSON response schema structure.
3. API initializes without Gemini API calls.
4. API initializes without existing PDFs or ChromaDB collections.
5. Invalid configuration raises a clear validation error.
6. Sensitive configuration values and API keys are never exposed.
"""

import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import app, create_app


@pytest.fixture
def client():
    """Provides FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


def test_health_endpoint_returns_200(client):
    """Test 1: Health endpoint returns HTTP 200."""
    response = client.get("/api/health")
    assert response.status_code == 200


def test_health_response_json_structure(client):
    """Test 2: Health response has the expected JSON structure."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    # Core metadata fields
    assert "status" in data
    assert data["status"] in ("ok", "degraded")
    assert "app_name" in data
    assert "environment" in data
    assert "version" in data
    assert "components" in data

    # Verify component map
    components = data["components"]
    assert isinstance(components, dict)
    expected_components = ["api", "database", "chroma_vector_store", "hypergraph_store", "llm_engine"]
    for comp in expected_components:
        assert comp in components, f"Missing component: {comp}"
        assert "status" in components[comp]
        assert "detail" in components[comp]
        assert isinstance(components[comp]["status"], str)
        assert isinstance(components[comp]["detail"], str)


def test_api_initialization_no_gemini_api_calls(monkeypatch):
    """
    Test 3: API can initialize and serve health checks without making Gemini API calls.
    Ensures that offline or air-gapped environments do not fail on startup.
    """
    call_tracker = {"called": False}

    def mock_forbidden_call(*args, **kwargs):
        call_tracker["called"] = True
        raise RuntimeError("External LLM API call was unexpectedly executed during health check!")

    # Attempt to monkeypatch any generativeai / genai methods if loaded
    monkeypatch.setattr("urllib.request.urlopen", mock_forbidden_call, raising=False)

    test_app = create_app()
    with TestClient(test_app) as test_client:
        res = test_client.get("/api/health")
        assert res.status_code == 200
        assert call_tracker["called"] is False


def test_api_initialization_without_pdfs_or_chromadb(tmp_path, monkeypatch):
    """
    Test 4: API initialization does not require uploaded PDFs or an existing ChromaDB collection.
    Tests clean startup in a brand-new unpopulated directory.
    """
    empty_data_dir = tmp_path / "empty_data"
    empty_data_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("backend.app.core.config.settings.data_dir", empty_data_dir)
    monkeypatch.setattr("backend.app.core.config.settings.database_path", empty_data_dir / "eduhyperrag.db")
    monkeypatch.setattr("backend.app.core.config.settings.knowledge_base_dir", empty_data_dir / "knowledge_base")
    monkeypatch.setattr("backend.app.core.config.settings.courses_data_dir", empty_data_dir / "courses")

    test_app = create_app()
    with TestClient(test_app) as test_client:
        res = test_client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        # Verify that uninitialized subsystems are reported accurately, not crashed
        assert data["components"]["database"]["status"] == "uninitialized"
        assert data["components"]["chroma_vector_store"]["status"] == "uninitialized"
        assert data["components"]["hypergraph_store"]["status"] == "uninitialized"


def test_invalid_configuration_raises_error():
    """Test 5: Invalid configuration produces a clear error."""
    with pytest.raises(ValueError) as exc_info:
        Settings(app_env="staging_unsupported")

    assert "Invalid APP_ENV" in str(exc_info.value)
    assert "development" in str(exc_info.value)


def test_sensitive_values_not_exposed(client, monkeypatch):
    """
    Test 6: Sensitive configuration values (e.g., API keys, tokens)
    are never exposed in health responses or error messages.
    """
    dummy_secret = "SECRET_GEMINI_KEY_999888777"
    monkeypatch.setattr("backend.app.core.config.settings.llm_api_key", dummy_secret)

    # 1. Check health endpoint response
    res = client.get("/api/health")
    assert res.status_code == 200
    assert dummy_secret not in res.text

    # 2. Check root endpoint response
    res_root = client.get("/")
    assert dummy_secret not in res_root.text

    # 3. Check 404 response
    res_404 = client.get("/api/nonexistent-route-for-testing")
    assert res_404.status_code == 404
    assert dummy_secret not in res_404.text
