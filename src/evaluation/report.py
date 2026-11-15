"""
Evaluation Report Engine for EduHyperRAG.
Aggregates benchmark metrics across the 6 pipeline architectures, computes comparative improvement percentages,
generates CSV/JSON results, and creates graphical visualization charts.
"""

import csv
import json
from pathlib import Path
from typing import Any, Dict, List
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt

from src.config import config
from src.evaluation.baselines import (
    EnhancedHyperRAGRunner,
    GraphRAGRunner,
    LightRAGRunner,
    OriginalHyperRAGRunner,
    TraditionalRAGRunner,
    VanillaLLMRunner,
)
from src.evaluation.dataset import load_benchmark_dataset
from src.evaluation.hallucination_checker import HallucinationChecker
from src.evaluation.metrics import (
    compute_generation_metrics,
    compute_retrieval_metrics,
)
from src.utils.file_io import save_json
from src.utils.logger import get_logger

logger = get_logger("evaluation_report")


class EvaluationReportEngine:
    """Orchestrates comparative benchmarking across all 6 architectures."""

    def __init__(self):
        self.eval_dir = config.project_root / "data" / "evaluation"
        self.eval_dir.mkdir(parents=True, exist_ok=True)
        self.checker = HallucinationChecker()

    def run_full_benchmark(self) -> Dict[str, Any]:
        """Runs all 6 pipelines on the 10 benchmark queries and computes comparative statistics."""
        dataset = load_benchmark_dataset()
        runners = [
            VanillaLLMRunner(),
            TraditionalRAGRunner(),
            GraphRAGRunner(),
            LightRAGRunner(),
            OriginalHyperRAGRunner(),
            EnhancedHyperRAGRunner(),
        ]

        logger.info(f"Starting Phase 9 Evaluation Benchmark ({len(runners)} architectures x {len(dataset)} questions)...")

        raw_results: List[Dict[str, Any]] = []
        aggregated_metrics: Dict[str, Dict[str, float]] = {}

        for runner in runners:
            logger.info(f"Evaluating Pipeline: {runner.name}...")
            r_metrics_list: List[Dict[str, float]] = []

            for q in dataset:
                run_out = runner.run_query(q.question)
                
                # Compute retrieval metrics
                precision, recall, kmr, completeness = compute_retrieval_metrics(
                    retrieved_chunk_ids=run_out["retrieved_chunk_ids"],
                    ground_truth_chunk_ids=q.ground_truth_chunk_ids,
                    retrieved_concept_names=run_out["retrieved_concepts"],
                    ground_truth_concepts=q.ground_truth_concepts,
                )

                # Run hallucination claim verification on generated answer
                ver_report = self.checker.verify_answer(
                    answer_text=run_out["answer"],
                    retrieved_chunks=run_out["chunks_data"],
                    retrieved_hyperedges=run_out["hyperedges_data"],
                    retrieved_concepts=run_out["concepts_data"],
                )

                # Compute generation and hallucination metrics
                (
                    correctness,
                    ans_completeness,
                    faithfulness,
                    relevance,
                    unsupported_rate,
                    her,
                    evidence_support_rate,
                ) = compute_generation_metrics(
                    generated_answer=run_out["answer"],
                    reference_answer=q.reference_answer,
                    query=q.question,
                    support_score=ver_report.support_score,
                    unsupported_claims_count=ver_report.unsupported_claims_count,
                    total_claims_count=len(ver_report.claims),
                )

                record = {
                    "architecture": runner.name,
                    "question_id": q.question_id,
                    "difficulty": q.difficulty,
                    "context_precision": precision,
                    "context_recall": recall,
                    "key_knowledge_missing_rate": kmr,
                    "retrieval_completeness": completeness,
                    "answer_correctness": correctness,
                    "answer_completeness": ans_completeness,
                    "faithfulness": faithfulness,
                    "relevance": relevance,
                    "unsupported_claim_rate": unsupported_rate,
                    "hallucination_error_rate": her,
                    "evidence_support_rate": evidence_support_rate,
                    "retrieval_latency_ms": run_out["retrieval_latency_ms"],
                    "generation_latency_ms": run_out["generation_latency_ms"],
                    "total_response_time_ms": run_out["total_response_time_ms"],
                    "iterations_count": run_out["iterations_count"],
                }
                raw_results.append(record)
                r_metrics_list.append(record)

            # Compute mean metrics for runner
            mean_dict = self._compute_mean_metrics(r_metrics_list)
            aggregated_metrics[runner.name] = mean_dict

        # Calculate comparative percentage improvements relative to baselines
        improvements = self._compute_improvements(aggregated_metrics)

        # Save CSV and JSON
        csv_path = self.eval_dir / "results.csv"
        json_path = self.eval_dir / "results.json"
        chart_path = self.eval_dir / "comparison_chart.png"

        self._save_csv(raw_results, csv_path)

        benchmark_export = {
            "aggregated_metrics": aggregated_metrics,
            "improvements_vs_baselines": improvements,
            "detailed_query_results": raw_results,
        }
        save_json(benchmark_export, json_path)

        # Generate comparison graph
        self._generate_comparison_chart(aggregated_metrics, chart_path)

        logger.info(f"Phase 9 Benchmark completed. Results saved to CSV ({csv_path}), JSON ({json_path}), Chart ({chart_path}).")

        return benchmark_export

    def _compute_mean_metrics(self, records: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculates average metrics across all benchmark queries for a pipeline."""
        metric_keys = [
            "context_precision", "context_recall", "key_knowledge_missing_rate",
            "retrieval_completeness", "answer_correctness", "answer_completeness",
            "faithfulness", "relevance", "unsupported_claim_rate",
            "hallucination_error_rate", "evidence_support_rate",
            "retrieval_latency_ms", "generation_latency_ms",
            "total_response_time_ms", "iterations_count"
        ]
        means = {}
        for key in metric_keys:
            vals = [r[key] for r in records if key in r]
            means[key] = round(sum(vals) / len(vals), 4) if vals else 0.0
        return means

    def _compute_improvements(self, aggregated: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
        """
        Computes percentage improvements of Proposed Enhanced Hyper-RAG against each baseline:
        Improvement % = ((Enhanced - Baseline) / Baseline) * 100
        For error/missing metrics (KMR, HER, Unsupported Rate, Response Time), reduction % is reported.
        """
        enhanced = aggregated.get("Proposed Enhanced Hyper-RAG", {})
        improvements: Dict[str, Dict[str, float]] = {}

        for b_name, b_metrics in aggregated.items():
            if b_name == "Proposed Enhanced Hyper-RAG":
                continue

            imp_dict: Dict[str, float] = {}
            for key, val in enhanced.items():
                b_val = b_metrics.get(key, 0.0)
                if b_val == 0.0:
                    pct = 100.0 if val > 0 else 0.0
                else:
                    pct = ((val - b_val) / b_val) * 100.0
                
                # For error metrics, negative change is an improvement (reduction)
                if key in ["key_knowledge_missing_rate", "hallucination_error_rate", "unsupported_claim_rate", "total_response_time_ms"]:
                    pct = -pct

                imp_dict[key] = round(pct, 2)
            improvements[b_name] = imp_dict

        return improvements

    def _save_csv(self, records: List[Dict[str, Any]], csv_path: Path) -> None:
        """Saves detailed query evaluation records to CSV."""
        if not records:
            return
        keys = list(records[0].keys())
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(records)

    def _generate_comparison_chart(self, aggregated: Dict[str, Dict[str, float]], chart_path: Path) -> None:
        """Generates matplotlib comparative bar chart across key metrics."""
        architectures = list(aggregated.keys())
        short_names = ["Vanilla", "RAG", "GraphRAG", "LightRAG", "Hyper-RAG", "Enhanced"]
        
        accuracy = [aggregated[a]["answer_correctness"] for a in architectures]
        faithfulness = [aggregated[a]["faithfulness"] for a in architectures]
        kmr = [aggregated[a]["key_knowledge_missing_rate"] for a in architectures]
        her = [aggregated[a]["hallucination_error_rate"] for a in architectures]

        x = range(len(short_names))
        width = 0.2

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar([i - 1.5*width for i in x], accuracy, width, label="Answer Correctness", color="#2b5c8f")
        ax.bar([i - 0.5*width for i in x], faithfulness, width, label="Faithfulness", color="#2e7d32")
        ax.bar([i + 0.5*width for i in x], kmr, width, label="Knowledge Missing (KMR)", color="#d84315")
        ax.bar([i + 1.5*width for i in x], her, width, label="Hallucination Error (HER)", color="#c62828")

        ax.set_ylabel("Score (0.0 to 1.0)", fontsize=11, fontweight="bold")
        ax.set_title("EduHyperRAG: Comparative Evaluation Across 6 Architectures", fontsize=13, fontweight="bold")
        ax.set_xticks(list(x))
        ax.set_xticklabels(short_names, fontsize=10)
        ax.legend(loc="upper left")
        ax.grid(axis="y", linestyle="--", alpha=0.5)

        plt.tight_layout()
        plt.savefig(chart_path, dpi=300)
        plt.close()
