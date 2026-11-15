"""
Unit tests for Phase 8 Explainability Engine and Display Data Models.
"""

import pytest

from src.agents.explanation_agent import EduExplainabilityEngine
from src.agents.state import VerificationAgentState
from src.evaluation.hallucination_checker import AnswerVerificationReport, ClaimVerificationResult
from src.generation.explanation import (
    ClaimEvidenceDisplay,
    ExplainabilityReport,
    SourceChunkDisplay,
    SupportingConceptDisplay,
    SupportingHyperedgeDisplay,
)


def test_explainability_report_markdown():
    report = ExplainabilityReport(
        query="How does water split in photosynthesis?",
        answer="Water photolysis occurs in PSII [chunk_001].",
        confidence_level="High",
        confidence_score=0.88,
        supporting_concepts=[
            SupportingConceptDisplay(name="Water", entity_type="Molecule", description="H2O")
        ],
        supporting_hyperedges=[
            SupportingHyperedgeDisplay(
                hyperedge_id="H1", label="water_photolysis", cardinality=3, concepts=["Water", "P680", "PSII"], description="Splitting water"
            )
        ],
        source_chunks=[
            SourceChunkDisplay(chunk_id="chunk_001", source_file="photosynthesis.txt", snippet="P680 splits water.")
        ],
        claim_evidences=[
            ClaimEvidenceDisplay(claim="Water photolysis occurs in PSII.", status="supported", score=1.0, supporting_excerpts=["Chunk chunk_001"])
        ],
        verification_badges=["✓ Evidence verified", "✓ No unsupported claims detected"],
    )

    md = report.to_markdown()
    assert "How does water split in photosynthesis?" in md
    assert "High (0.88)" in md
    assert "Water" in md
    assert "{Water, P680, PSII}" in md
    assert "✓ Evidence verified" in md
    assert "chain-of-thought" not in md.lower()


def test_explainability_engine_sufficient():
    engine = EduExplainabilityEngine()
    verified_state: VerificationAgentState = {
        "user_query": "Role of Rubisco",
        "extracted_query_concepts": ["rubisco"],
        "retrieved_chunks": [{"chunk_id": "c1", "content": "Rubisco fixes CO2.", "metadata": {"source_file": "bio.txt"}}],
        "retrieved_hyperedges": [{"hyperedge_id": "H1", "label": "fixation", "cardinality": 3, "concepts": ["Rubisco", "CO2", "RuBP"], "description": "Fixation"}],
        "retrieved_concepts": [{"name": "Rubisco", "entity_type": "Enzyme", "description": "Carboxylase"}],
        "sources": ["c1"],
        "is_sufficient": True,
        "verification_reasoning": "Evidence verified.",
        "relevance_score": 0.8,
        "missing_concepts": [],
        "confidence": 0.85,
        "iteration_count": 1,
        "max_iterations": 2,
        "status": "VERIFIED",
    }

    answer_result = {
        "answer": "Rubisco catalyzes CO2 fixation onto RuBP [c1].",
        "supporting_chunks": ["c1"],
        "supporting_hyperedges": ["H1"],
        "confidence": 0.85,
        "unsupported_claims": [],
    }

    report_ver = AnswerVerificationReport(
        answer=answer_result["answer"],
        claims=[ClaimVerificationResult(claim="Rubisco catalyzes CO2 fixation.", status="supported", evidence=["c1"], score=1.0)],
        support_score=1.0,
        unsupported_claims_count=0,
        decision="ACCEPT",
        feedback="Accepted",
    )

    exp = engine.generate_explanation(verified_state, answer_result, report_ver)
    assert exp.confidence_level == "High"
    assert len(exp.supporting_concepts) == 1
    assert exp.supporting_concepts[0].name == "Rubisco"
    assert len(exp.supporting_hyperedges) == 1
    assert "[OK] Evidence verified" in exp.verification_badges
