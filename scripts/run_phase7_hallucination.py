"""
Script to execute Phase 7: Hallucination Detection and Claim Verification.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents.verification_graph import run_agentic_verification
from src.evaluation.hallucination_checker import HallucinationChecker
from src.generation.answer_generator import EducationalAnswerGenerator
from src.utils.logger import get_logger

logger = get_logger("run_phase7")


def main():
    print("=" * 85)
    print("      EDUHYPERRAG - PHASE 7: HALLUCINATION DETECTION & CLAIM VERIFICATION      ")
    print("=" * 85)

    checker = HallucinationChecker(min_support_score=0.70, max_unsupported_ratio=0.25)
    answer_generator = EducationalAnswerGenerator()

    # TEST CASE 1: Valid Grounded Answer Verification
    print("\n" + "=" * 85)
    print("TEST CASE 1: GROUNDED ANSWER VERIFICATION")
    query_1 = "How does water photolysis work in Photosystem II to produce oxygen?"
    print(f"Query: \"{query_1}\"")
    print("=" * 85)

    verified_state_1 = run_agentic_verification(user_query=query_1, max_iterations=2)
    answer_1_dict = answer_generator.generate_answer(verified_state_1)

    report_1 = checker.verify_answer(
        answer_text=answer_1_dict["answer"],
        retrieved_chunks=verified_state_1["retrieved_chunks"],
        retrieved_hyperedges=verified_state_1["retrieved_hyperedges"],
        retrieved_concepts=verified_state_1["retrieved_concepts"],
    )

    print("\n--- CLAIM-BY-CLAIM VERIFICATION (CASE 1) ---")
    for c_idx, claim in enumerate(report_1.claims, 1):
        print(f"Claim {c_idx} : \"{claim.claim}\"")
        print(f"   Status  : [{claim.status.upper()}] (Score: {claim.score})")
        print(f"   Evidence: {claim.evidence}\n")

    print("-" * 85)
    print(f"Overall Support Score   : {report_1.support_score}")
    print(f"Unsupported Claims Count: {report_1.unsupported_claims_count}")
    print(f"Final System Decision   : {report_1.decision}")
    print(f"Verification Feedback   : {report_1.feedback}")
    print("-" * 85)

    # TEST CASE 2: Intentionally Unsupported / Hallucinated Answer Verification
    print("\n" + "=" * 85)
    print("TEST CASE 2: INTENTIONALLY UNSUPPORTED / HALLUCINATED ANSWER")
    query_2 = "What pigments are involved in light absorption?"
    hallucinated_answer = (
        "Chlorophyll a and Chlorophyll b absorb light in thylakoid membranes.\n"
        "Photosynthesis in plants generates synthetic jet fuel and titanium dioxide crystals under nuclear radiation."
    )
    print(f"Query: \"{query_2}\"")
    print(f"Simulated Generated Answer:\n{hallucinated_answer}")
    print("=" * 85)

    verified_state_2 = run_agentic_verification(user_query=query_2, max_iterations=2)
    report_2 = checker.verify_answer(
        answer_text=hallucinated_answer,
        retrieved_chunks=verified_state_2["retrieved_chunks"],
        retrieved_hyperedges=verified_state_2["retrieved_hyperedges"],
        retrieved_concepts=verified_state_2["retrieved_concepts"],
    )

    print("\n--- CLAIM-BY-CLAIM VERIFICATION (CASE 2) ---")
    for c_idx, claim in enumerate(report_2.claims, 1):
        print(f"Claim {c_idx} : \"{claim.claim}\"")
        print(f"   Status  : [{claim.status.upper()}] (Score: {claim.score})")
        print(f"   Evidence: {claim.evidence}\n")

    print("-" * 85)
    print(f"Overall Support Score   : {report_2.support_score}")
    print(f"Unsupported Claims Count: {report_2.unsupported_claims_count}")
    print(f"Final System Decision   : {report_2.decision}")
    print(f"Verification Feedback   : {report_2.feedback}")
    print("-" * 85)

    print("\nPhase 7 completed successfully!")


if __name__ == "__main__":
    main()
