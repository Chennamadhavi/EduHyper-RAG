"""
Evaluation Metrics Calculator for EduHyperRAG.
Computes quantitative scores across Retrieval, Generation, Hallucination, and System Latency.
"""

import re
import time
from typing import Any, Dict, List, Set, Tuple
from pydantic import BaseModel, Field


class EvaluationMetricsResult(BaseModel):
    """Container for computed evaluation metrics for a single query run."""

    # Retrieval Metrics
    context_precision: float
    context_recall: float
    key_knowledge_missing_rate: float  # KMR = 1 - context_recall
    retrieval_completeness: float

    # Generation Metrics
    answer_correctness: float
    answer_completeness: float
    faithfulness: float
    relevance: float

    # Hallucination Metrics
    unsupported_claim_rate: float
    hallucination_error_rate: float  # HER = 1 - faithfulness
    evidence_support_rate: float

    # System Metrics
    retrieval_latency_ms: float
    generation_latency_ms: float
    total_response_time_ms: float
    iterations_count: int


def compute_retrieval_metrics(
    retrieved_chunk_ids: List[str],
    ground_truth_chunk_ids: List[str],
    retrieved_concept_names: List[str],
    ground_truth_concepts: List[str],
) -> Tuple[float, float, float, float]:
    """Calculates context_precision, context_recall, KMR, and retrieval_completeness."""
    ret_set = set(retrieved_chunk_ids)
    gt_set = set(ground_truth_chunk_ids)

    if not ret_set:
        precision = 0.0
    else:
        intersection = ret_set.intersection(gt_set)
        precision = len(intersection) / len(ret_set)

    if not gt_set:
        recall = 1.0
    else:
        intersection = ret_set.intersection(gt_set)
        recall = len(intersection) / len(gt_set)

    kmr = max(0.0, 1.0 - recall)

    # Concept completeness
    gt_c_set = {c.lower() for c in ground_truth_concepts}
    ret_c_set = {c.lower() for c in retrieved_concept_names}

    if not gt_c_set:
        completeness = 1.0
    else:
        completeness = len(ret_c_set.intersection(gt_c_set)) / len(gt_c_set)

    return (
        round(precision, 4),
        round(recall, 4),
        round(kmr, 4),
        round(completeness, 4),
    )


def compute_generation_metrics(
    generated_answer: str,
    reference_answer: str,
    query: str,
    support_score: float,
    unsupported_claims_count: int,
    total_claims_count: int,
) -> Tuple[float, float, float, float, float, float, float]:
    """
    Calculates answer_correctness, answer_completeness, faithfulness, relevance,
    unsupported_claim_rate, HER, and evidence_support_rate.
    """
    gen_words = set(re.findall(r"\b\w+\b", generated_answer.lower()))
    ref_words = set(re.findall(r"\b\w+\b", reference_answer.lower()))
    query_words = set(re.findall(r"\b\w+\b", query.lower()))

    # Answer correctness (word Jaccard similarity)
    if not gen_words or not ref_words:
        correctness = 0.0
    else:
        correctness = len(gen_words.intersection(ref_words)) / len(gen_words.union(ref_words))

    # Answer completeness (reference word recall)
    if not ref_words:
        completeness = 1.0
    else:
        completeness = len(gen_words.intersection(ref_words)) / len(ref_words)

    # Relevance (query terms present in generated answer)
    stop_words = {"what", "is", "the", "role", "of", "how", "does", "do", "in", "and", "to", "are"}
    meaningful_q_words = query_words - stop_words
    if not meaningful_q_words:
        relevance = 1.0
    else:
        relevance = len(gen_words.intersection(meaningful_q_words)) / len(meaningful_q_words)

    # Faithfulness & Hallucination rates
    faithfulness = max(0.0, min(1.0, support_score))
    her = max(0.0, 1.0 - faithfulness)

    if total_claims_count > 0:
        unsupported_rate = unsupported_claims_count / total_claims_count
        evidence_support_rate = (total_claims_count - unsupported_claims_count) / total_claims_count
    else:
        unsupported_rate = 0.0
        evidence_support_rate = 1.0 if "insufficient evidence" not in generated_answer.lower() else 0.0

    return (
        round(correctness, 4),
        round(completeness, 4),
        round(faithfulness, 4),
        round(relevance, 4),
        round(unsupported_rate, 4),
        round(her, 4),
        round(evidence_support_rate, 4),
    )
