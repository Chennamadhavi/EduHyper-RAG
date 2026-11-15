"""
Script to execute Phase 6: Grounded Educational Answer Generation.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents.verification_graph import run_agentic_verification
from src.generation.answer_generator import EducationalAnswerGenerator
from src.utils.logger import get_logger

logger = get_logger("run_phase6")


def main():
    print("=" * 85)
    print("      EDUHYPERRAG - PHASE 6: GROUNDED EDUCATIONAL ANSWER GENERATION      ")
    print("=" * 85)

    answer_generator = EducationalAnswerGenerator()

    test_queries = [
        "How does water split during light reactions in Photosystem II?",
        "What is the role of Rubisco in the Calvin cycle?",
        "How do C4 plants suppress photorespiration compared to C3 plants?",
        "What is the mechanism of dark matter annihilation in black hole thermodynamics?",
    ]

    for idx, query in enumerate(test_queries, 1):
        print("\n" + "=" * 85)
        print(f"QUESTION {idx}: \"{query}\"")
        print("=" * 85)

        # Step 1: Execute Phase 5 Agentic Verification Workflow
        verified_state = run_agentic_verification(user_query=query, max_iterations=2)

        # Display Retrieved & Verified Evidence Summary
        print("\n--- 1. RETRIEVED EVIDENCE SUMMARY ---")
        print(f"Accumulated Chunks     : {len(verified_state['retrieved_chunks'])}")
        print(f"Accumulated Hyperedges : {len(verified_state['retrieved_hyperedges'])}")
        print(f"Accumulated Concepts   : {len(verified_state['retrieved_concepts'])}")

        print("\n--- 2. VERIFIED EVIDENCE AGENT RESULT (PHASE 5) ---")
        print(f"Agent Status          : {verified_state['status']}")
        print(f"Is Sufficient?        : {verified_state['is_sufficient']}")
        print(f"Relevance Score       : {verified_state['relevance_score']}")
        print(f"Confidence            : {verified_state['confidence']}")
        print(f"Verification Reasoning: {verified_state['verification_reasoning']}")

        # Step 2: Execute Phase 6 Answer Generation
        answer_result = answer_generator.generate_answer(verified_state)

        print("\n--- 3. FINAL GROUNDED ANSWER (PHASE 6) ---")
        print(f"Answer Content:\n{answer_result['answer']}\n")
        print(f"Supporting Chunk IDs    : {answer_result['supporting_chunks']}")
        print(f"Supporting Hyperedges   : {answer_result['supporting_hyperedges']}")
        print(f"Generation Confidence   : {answer_result['confidence']}")
        print(f"Unsupported Claims      : {answer_result['unsupported_claims']}")
        print("-" * 85)

    print("\nPhase 6 completed successfully!")


if __name__ == "__main__":
    main()
