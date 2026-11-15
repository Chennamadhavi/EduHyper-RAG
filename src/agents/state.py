"""
Agent State Schema for LangGraph Agentic Verification Workflow.

Tracks:
- User query
- Course/document scope
- Retrieved evidence
- Verification reasoning
- Missing concepts
- Confidence
- Iteration count
- Loop safety bounds

The state is subject-agnostic and supports retrieval isolation
at both document and course levels.
"""

from typing import Any, Dict, List, Optional

from typing_extensions import TypedDict


class VerificationAgentState(TypedDict, total=False):
    """
    LangGraph State Dictionary for Evidence Verification Workflow.

    Scope rules:

    - doc_id identifies one uploaded document/PDF.
    - course_id identifies the course containing the document(s).
    - When both are available, doc_id takes priority.
    - Retrieval components must never use unrelated global
      document knowledge when a scope is available.
    """

    # =========================================================
    # QUERY & SCOPE
    # =========================================================

    # Student's original question.
    user_query: str

    # Course containing the uploaded educational material.
    #
    # Used for course-level retrieval isolation when doc_id
    # is not available.
    course_id: Optional[str]

    # Specific uploaded document/PDF.
    #
    # When available, this takes priority over course_id.
    doc_id: Optional[str]

    # Concepts extracted from the user's question.
    extracted_query_concepts: List[str]

    # =========================================================
    # EVIDENCE REPOSITORIES
    # =========================================================

    # Retrieved semantic/vector chunks.
    retrieved_chunks: List[
        Dict[str, Any]
    ]

    # Retrieved hyperedges from the document-specific
    # hypergraph.
    retrieved_hyperedges: List[
        Dict[str, Any]
    ]

    # Retrieved concepts from the document-specific
    # hypergraph.
    retrieved_concepts: List[
        Dict[str, Any]
    ]

    # Combined source chunk IDs.
    sources: List[str]

    # =========================================================
    # RETRIEVAL INFORMATION
    # =========================================================

    # Summary returned by HybridRetriever.
    #
    # This is useful for debugging and displaying retrieval
    # scope information in the UI.
    retrieval_summary: Dict[str, Any]

    # =========================================================
    # VERIFICATION OUTPUTS
    # =========================================================

    # Whether retrieved evidence is sufficient.
    is_sufficient: bool

    # Explanation produced by the verification agent.
    verification_reasoning: str

    # Relevance score of retrieved evidence.
    relevance_score: float

    # Concepts that were not sufficiently supported.
    missing_concepts: List[str]

    # Overall confidence value.
    confidence: float

    # =========================================================
    # GENERATION OUTPUTS
    # =========================================================

    # Final generated answer.
    final_answer: str

    # Verification result for the generated answer.
    verification_result: str

    # Number of unsupported claims detected.
    unsupported_claims: List[str]

    # =========================================================
    # EXECUTION & SAFETY CONTROL
    # =========================================================

    # Current verification/retrieval iteration.
    iteration_count: int

    # Maximum number of allowed iterations.
    max_iterations: int

    # Current workflow status.
    #
    # Examples:
    #
    # INITIALIZED
    # RETRIEVING
    # RETRIEVED
    # VERIFYING
    # VERIFIED
    # INSUFFICIENT
    # REGENERATE
    # MAX_ITERATIONS_REACHED
    # RETRIEVAL_ERROR
    # GENERATION_ERROR
    status: str