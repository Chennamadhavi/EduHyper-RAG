"""
Unit tests for Phase 6 Educational Answer Generator.
"""

import pytest

from src.agents.state import VerificationAgentState
from src.generation.answer_generator import EducationalAnswerGenerator, AnswerOutput


def test_answer_output_schema():
    out = AnswerOutput(
        answer="Water is split by PSII [chunk_001].",
        supporting_chunks=["chunk_001"],
        supporting_hyperedges=["H1"],
        confidence=0.9,
        unsupported_claims=[],
    )
    assert out.supporting_chunks == ["chunk_001"]
    assert out.confidence == 0.9
    assert out.unsupported_claims == []


def test_generator_sufficient_state():
    generator = EducationalAnswerGenerator(api_key="")
    verified_state: VerificationAgentState = {
        "user_query": "How does water photolysis work in Photosystem II?",
        "extracted_query_concepts": ["water photolysis", "photosystem ii"],
        "retrieved_chunks": [
            {
                "chunk_id": "photosynthesis_chapter_semantic_0001",
                "content": "P680 extracts electrons from water molecules via Oxygen-Evolving Complex: 2 H2O -> 4 H+ + 4 e- + O2.",
                "relevance_score": 0.85,
                "retrieval_method": "semantic",
            }
        ],
        "retrieved_hyperedges": [
            {
                "hyperedge_id": "psii_water_splitting_complex",
                "label": "psii_water_splitting_complex",
                "cardinality": 3,
                "concepts": ["Photosystem II", "P680", "Oxygen-Evolving Complex"],
                "description": "Water photolysis mechanism.",
                "source_chunk_ids": ["photosynthesis_chapter_semantic_0001"],
            }
        ],
        "retrieved_concepts": [],
        "sources": ["photosynthesis_chapter_semantic_0001"],
        "is_sufficient": True,
        "verification_reasoning": "Sufficient evidence verified.",
        "relevance_score": 0.85,
        "missing_concepts": [],
        "confidence": 0.85,
        "iteration_count": 1,
        "max_iterations": 2,
        "status": "VERIFIED",
    }

    result = generator.generate_answer(verified_state)
    assert "answer" in result
    assert len(result["supporting_chunks"]) > 0
    assert result["confidence"] > 0.0
    assert result["unsupported_claims"] == []


def test_generator_insufficient_state_refusal():
    generator = EducationalAnswerGenerator(api_key="")
    insufficient_state: VerificationAgentState = {
        "user_query": "What is quantum gravity in black hole thermodynamics?",
        "extracted_query_concepts": ["quantum gravity", "black hole"],
        "retrieved_chunks": [],
        "retrieved_hyperedges": [],
        "retrieved_concepts": [],
        "sources": [],
        "is_sufficient": False,
        "verification_reasoning": "Missing concepts in knowledge base.",
        "relevance_score": 0.0,
        "missing_concepts": ["quantum gravity"],
        "confidence": 0.0,
        "iteration_count": 2,
        "max_iterations": 2,
        "status": "MAX_ITERATIONS_REACHED",
    }

    result = generator.generate_answer(insufficient_state)
    assert "insufficient evidence" in result["answer"].lower()
    assert result["confidence"] == 0.0
    assert result["supporting_chunks"] == []
