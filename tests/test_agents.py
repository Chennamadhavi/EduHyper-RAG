"""
Unit tests for Phase 5 LangGraph Agentic Verification Workflow.
"""

import tempfile
from pathlib import Path
import pytest

from src.agents.retrieval_agent import RetrievalAgentNode
from src.agents.state import VerificationAgentState
from src.agents.verification_agent import VerificationAgentNode
from src.agents.verification_graph import build_verification_graph, run_agentic_verification
from src.preprocessing.chunker import Chunk, ChunkingStrategy
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.hypergraph_retriever import HypergraphRetriever
from src.retrieval.semantic_retriever import SemanticRetriever
from src.utils.file_io import save_json


def test_verification_agent_node_sufficient():
    v_node = VerificationAgentNode()
    state: VerificationAgentState = {
        "user_query": "How does water photolysis work in Photosystem II?",
        "extracted_query_concepts": [],
        "retrieved_chunks": [
            {
                "chunk_id": "c1",
                "content": "Photosystem II P680 reaction center uses the Oxygen-Evolving Complex for water photolysis, releasing O2.",
                "relevance_score": 0.85,
                "retrieval_method": "semantic",
            }
        ],
        "retrieved_hyperedges": [
            {
                "hyperedge_id": "H1",
                "label": "water_splitting",
                "cardinality": 3,
                "concepts": ["Photosystem II", "P680", "Water Photolysis"],
                "description": "Water photolysis complex.",
                "source_chunk_ids": ["c1"],
            }
        ],
        "retrieved_concepts": [
            {"name": "Photosystem II", "description": "PSII complex", "source_chunk_ids": ["c1"]}
        ],
        "sources": ["c1"],
        "is_sufficient": False,
        "verification_reasoning": "",
        "relevance_score": 0.0,
        "missing_concepts": [],
        "confidence": 0.0,
        "iteration_count": 1,
        "max_iterations": 2,
        "status": "RETRIEVED",
    }

    res_state = v_node(state)
    assert res_state["is_sufficient"] is True
    assert res_state["status"] == "VERIFIED"
    assert res_state["confidence"] > 0.5


def test_verification_agent_node_insufficient():
    v_node = VerificationAgentNode()
    state: VerificationAgentState = {
        "user_query": "What is the exact mechanism of dark matter annihilation in cosmic microwave background radiation?",
        "extracted_query_concepts": [],
        "retrieved_chunks": [],
        "retrieved_hyperedges": [],
        "retrieved_concepts": [],
        "sources": [],
        "is_sufficient": False,
        "verification_reasoning": "",
        "relevance_score": 0.0,
        "missing_concepts": [],
        "confidence": 0.0,
        "iteration_count": 2,
        "max_iterations": 2,
        "status": "RETRIEVED",
    }

    res_state = v_node(state)
    assert res_state["is_sufficient"] is False
    assert res_state["status"] == "MAX_ITERATIONS_REACHED"
    assert "dark matter" in " ".join(res_state["missing_concepts"]).lower() or "cosmic" in " ".join(res_state["missing_concepts"]).lower()


def test_langgraph_workflow_loop_safety():
    # Test that the graph terminates after max_iterations for an out-of-domain query
    final_state = run_agentic_verification(
        user_query="Nonexistent unknown alien topic xyz 123",
        max_iterations=2
    )

    assert final_state["is_sufficient"] is False
    assert final_state["status"] == "MAX_ITERATIONS_REACHED"
    assert final_state["iteration_count"] <= 2
