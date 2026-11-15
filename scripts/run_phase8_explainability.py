"""
Script to execute Phase 8: Explainability and Evidence Display.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents.explanation_agent import EduExplainabilityEngine
from src.agents.verification_graph import run_agentic_verification
from src.evaluation.hallucination_checker import HallucinationChecker
from src.generation.answer_generator import EducationalAnswerGenerator
from src.utils.logger import get_logger

logger = get_logger("run_phase8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 85)
    print("      EDUHYPERRAG - PHASE 8: EXPLAINABILITY AND EVIDENCE DISPLAY      ")
    print("=" * 85)

    checker = HallucinationChecker()
    answer_generator = EducationalAnswerGenerator()
    explanation_engine = EduExplainabilityEngine()

    test_queries = [
        "How does water contribute to photosynthesis?",
        "What is the role of Rubisco in the Calvin cycle?",
        "What is the mechanism of dark matter annihilation in black hole thermodynamics?",
    ]

    for idx, query in enumerate(test_queries, 1):
        print("\n" + "=" * 85)
        print(f"QUERY {idx}: \"{query}\"")
        print("=" * 85)

        # 1. Phase 5: Verification Workflow
        verified_state = run_agentic_verification(user_query=query, max_iterations=2)

        # 2. Phase 6: Answer Generation
        answer_result = answer_generator.generate_answer(verified_state)

        # 3. Phase 7: Hallucination Verification
        verification_report = checker.verify_answer(
            answer_text=answer_result["answer"],
            retrieved_chunks=verified_state["retrieved_chunks"],
            retrieved_hyperedges=verified_state["retrieved_hyperedges"],
            retrieved_concepts=verified_state["retrieved_concepts"],
        )

        # 4. Phase 8: Explainability Report Generation
        explainability_report = explanation_engine.generate_explanation(
            verified_state=verified_state,
            answer_result=answer_result,
            verification_report=verification_report,
        )

        # Render Formatted UI Output
        print("\n--- SYSTEM RESPONSE & EXPLAINABILITY DISPLAY ---")
        print(explainability_report.to_markdown())
        print("-" * 85)

    print("\nPhase 8 completed successfully!")


if __name__ == "__main__":
    main()
