"""
Unit tests for Phase 7 Hallucination Checker and Claim Verification Engine.
"""

import pytest
from src.evaluation.hallucination_checker import HallucinationChecker


def test_supported_claim_verification():
    checker = HallucinationChecker(min_support_score=0.70)
    answer = "Photosystem II reaction center P680 splits water into oxygen and protons."
    chunks = [
        {
            "chunk_id": "c1",
            "content": "Photosystem II reaction center P680 extracts electrons from water molecules, releasing oxygen and protons."
        }
    ]
    
    report = checker.verify_answer(
        answer_text=answer,
        retrieved_chunks=chunks,
        retrieved_hyperedges=[],
    )

    assert report.decision == "ACCEPT"
    assert report.support_score >= 0.70
    assert report.unsupported_claims_count == 0
    assert report.claims[0].status == "supported"
    assert len(report.claims[0].evidence) > 0


def test_unsupported_claim_detection():
    checker = HallucinationChecker(min_support_score=0.70, max_unsupported_ratio=0.25)
    answer = "Photosynthesis produces synthetic jet fuel and titanium dioxide crystals in leaf cells."
    chunks = [
        {
            "chunk_id": "c1",
            "content": "Photosynthesis converts solar light into chemical energy stored in glucose."
        }
    ]

    report = checker.verify_answer(
        answer_text=answer,
        retrieved_chunks=chunks,
        retrieved_hyperedges=[],
    )

    assert report.decision == "REGENERATE"
    assert report.unsupported_claims_count >= 1
    assert report.support_score < 0.70
    assert report.claims[0].status == "unsupported"


def test_refusal_answer_verification():
    checker = HallucinationChecker()
    answer = "Based on the provided educational materials, there is insufficient evidence to answer this question."
    
    report = checker.verify_answer(
        answer_text=answer,
        retrieved_chunks=[],
        retrieved_hyperedges=[],
    )

    assert report.decision == "ACCEPT"
    assert report.support_score == 1.0
    assert report.unsupported_claims_count == 0
