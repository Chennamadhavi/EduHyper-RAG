"""
Unit tests for Phase 9 Evaluation Framework.
"""

import tempfile
from pathlib import Path
import pytest

from src.evaluation.dataset import load_benchmark_dataset
from src.evaluation.metrics import (
    compute_generation_metrics,
    compute_retrieval_metrics,
)
from src.evaluation.report import EvaluationReportEngine


def test_load_benchmark_dataset():
    dataset = load_benchmark_dataset()
    assert len(dataset) == 10
    assert dataset[0].question_id == "Q01"
    assert "photosynthesis" in dataset[0].reference_answer.lower()


def test_compute_retrieval_metrics():
    precision, recall, kmr, completeness = compute_retrieval_metrics(
        retrieved_chunk_ids=["c1", "c2"],
        ground_truth_chunk_ids=["c1"],
        retrieved_concept_names=["Photosystem II", "P680"],
        ground_truth_concepts=["Photosystem II"],
    )
    assert precision == 0.5
    assert recall == 1.0
    assert kmr == 0.0
    assert completeness == 1.0


def test_compute_generation_metrics():
    (
        correctness,
        completeness,
        faithfulness,
        relevance,
        unsupported_rate,
        her,
        evidence_support_rate,
    ) = compute_generation_metrics(
        generated_answer="Water photolysis splits H2O in Photosystem II.",
        reference_answer="Water photolysis splits H2O in Photosystem II.",
        query="How does water photolysis work?",
        support_score=0.9,
        unsupported_claims_count=0,
        total_claims_count=1,
    )
    assert correctness == 1.0
    assert faithfulness == 0.9
    assert her == 0.1
    assert unsupported_rate == 0.0
    assert evidence_support_rate == 1.0


def test_evaluation_report_engine():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_path = Path(tmp_dir)
        engine = EvaluationReportEngine()
        engine.eval_dir = tmp_path

        from src.config import config
        orig_knowledge_base = config.knowledge_base_dir
        
        try:
            benchmark_out = engine.run_full_benchmark()
            assert "aggregated_metrics" in benchmark_out
            assert "improvements_vs_baselines" in benchmark_out
            assert (tmp_path / "results.csv").exists()
            assert (tmp_path / "results.json").exists()
            assert (tmp_path / "comparison_chart.png").exists()
        finally:
            config.knowledge_base_dir = orig_knowledge_base
