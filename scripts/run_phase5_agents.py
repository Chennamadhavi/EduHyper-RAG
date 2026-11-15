"""
Script to execute Phase 5: Agentic Evidence Verification Workflow using LangGraph.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.agents.verification_graph import run_agentic_verification
from src.utils.logger import get_logger

logger = get_logger("run_phase5")


def main():
    print("=" * 85)
    print("      EDUHYPERRAG - PHASE 5: AGENTIC EVIDENCE VERIFICATION (LANGGRAPH)     ")
    print("=" * 85)

    test_scenarios = [
        {
            "category": "SUFFICIENT EVIDENCE QUERY",
            "query": "How does water photolysis work in Photosystem II to produce oxygen?",
        },
        {
            "category": "MISSING / OUT-OF-DOMAIN EVIDENCE QUERY",
            "query": "What is the mathematical formulation of quantum gravity in black hole thermodynamics?",
        },
    ]

    for idx, scenario in enumerate(test_scenarios, 1):
        print("\n" + "=" * 85)
        print(f"SCENARIO {idx}: [{scenario['category']}]")
        print(f"Query: \"{scenario['query']}\"")
        print("=" * 85)

        final_state = run_agentic_verification(
            user_query=scenario["query"],
            max_iterations=2
        )

        print("\n--- LANGGRAPH VERIFICATION AGENT EXECUTION RESULT ---")
        print(f"Final Status             : {final_state['status']}")
        print(f"Is Evidence Sufficient?  : {final_state['is_sufficient']}")
        print(f"Relevance Score          : {final_state['relevance_score']}")
        print(f"Confidence               : {final_state['confidence']}")
        print(f"Total Iterations Executed: {final_state['iteration_count']} / {final_state['max_iterations']}")
        print(f"Extracted Query Concepts : {final_state['extracted_query_concepts']}")
        print(f"Missing Concepts         : {final_state['missing_concepts']}")
        print(f"Verification Reasoning   : {final_state['verification_reasoning']}")
        print(f"Accumulated Chunks Count : {len(final_state['retrieved_chunks'])}")
        print(f"Accumulated Hyperedges   : {len(final_state['retrieved_hyperedges'])}")
        print(f"Supported Source Chunks  : {final_state['sources']}")
        print("-" * 85)

    print("\nPhase 5 completed successfully!")


if __name__ == "__main__":
    main()
