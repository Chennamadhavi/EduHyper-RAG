"""
Script to execute Phase 9: Evaluation Against RAG, GraphRAG, LightRAG, and Hyper-RAG.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.evaluation.report import EvaluationReportEngine
from src.utils.logger import get_logger

logger = get_logger("run_phase9")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 95)
    print("      EDUHYPERRAG - PHASE 9: SYSTEM EVALUATION & BENCHMARK COMPARISON      ")
    print("=" * 95)

    report_engine = EvaluationReportEngine()
    benchmark_out = report_engine.run_full_benchmark()

    aggregated = benchmark_out["aggregated_metrics"]
    improvements = benchmark_out["improvements_vs_baselines"]

    print("\n" + "=" * 95)
    print("                      COMPARATIVE BENCHMARK EVALUATION TABLE                      ")
    print("=" * 95)
    print(f"{'Architecture':<28} | {'Correctness':<11} | {'Faithfulness':<12} | {'Recall':<8} | {'KMR':<6} | {'HER':<6} | {'Latency(ms)':<11}")
    print("-" * 95)

    for arch_name, m in aggregated.items():
        print(
            f"{arch_name:<28} | "
            f"{m['answer_correctness']:<11.4f} | "
            f"{m['faithfulness']:<12.4f} | "
            f"{m['context_recall']:<8.4f} | "
            f"{m['key_knowledge_missing_rate']:<6.4f} | "
            f"{m['hallucination_error_rate']:<6.4f} | "
            f"{m['total_response_time_ms']:<11.2f}"
        )
    print("-" * 95)

    print("\n" + "=" * 95)
    print("       PROPOSED ENHANCED HYPER-RAG PERCENTAGE IMPROVEMENTS VS BASELINES       ")
    print("=" * 95)
    for b_name, imp in improvements.items():
        print(f"--- Improvement vs {b_name} ---")
        print(f"  * Answer Correctness    : {imp['answer_correctness']:+.2f}%")
        print(f"  * Faithfulness          : {imp['faithfulness']:+.2f}%")
        print(f"  * Context Recall        : {imp['context_recall']:+.2f}%")
        print(f"  * KMR Reduction         : {imp['key_knowledge_missing_rate']:+.2f}%")
        print(f"  * HER Reduction         : {imp['hallucination_error_rate']:+.2f}%")
        print(f"  * Total Latency Change  : {imp['total_response_time_ms']:+.2f}% (Note: Multi-step agentic loop increases latency)")
        print()

    print("=" * 95)
    print("OUTPUT ARTIFACTS GENERATED:")
    print(f"1. Detailed Results CSV : {report_engine.eval_dir / 'results.csv'}")
    print(f"2. Aggregated JSON      : {report_engine.eval_dir / 'results.json'}")
    print(f"3. Comparison PNG Chart : {report_engine.eval_dir / 'comparison_chart.png'}")
    print("=" * 95)

    print("\nPhase 9 completed successfully!")


if __name__ == "__main__":
    main()
