"""
LangGraph Workflow for Agentic Evidence Verification.

Workflow:

    Retrieval -> Verification
          ^         |
          |_________|

The workflow supports:

- Course-level retrieval isolation
- Document-level retrieval isolation
- Iterative retrieval using missing concepts
- Evidence accumulation
- Maximum iteration safety
- Subject/domain-independent retrieval
- Document-specific hypergraph retrieval
"""

from typing import Optional

from langgraph.graph import END, StateGraph

from src.agents.retrieval_agent import RetrievalAgentNode
from src.agents.state import VerificationAgentState
from src.agents.verification_agent import VerificationAgentNode
from src.retrieval.hybrid_retriever import HybridRetriever
from src.utils.logger import get_logger


logger = get_logger("verification_graph")


# ============================================================
# CONDITIONAL ROUTING
# ============================================================


def should_continue(
    state: VerificationAgentState,
) -> str:
    """
    Decide whether the workflow should finish or perform
    another retrieval pass.

    Routing rules:

    1. If evidence is sufficient -> END.
    2. If maximum iterations reached -> END.
    3. Otherwise -> retrieval for another evidence pass.
    """

    is_sufficient = state.get(
        "is_sufficient",
        False,
    )

    iteration_count = state.get(
        "iteration_count",
        0,
    )

    max_iterations = state.get(
        "max_iterations",
        2,
    )

    # --------------------------------------------------------
    # Evidence is sufficient
    # --------------------------------------------------------

    if is_sufficient:

        logger.info(
            "Routing decision: END "
            "(Evidence Verified Sufficient)"
        )

        return END

    # --------------------------------------------------------
    # Safety limit
    # --------------------------------------------------------

    if iteration_count >= max_iterations:

        logger.info(
            "Routing decision: END "
            f"(Maximum iterations "
            f"{max_iterations} reached)"
        )

        return END

    # --------------------------------------------------------
    # More evidence required
    # --------------------------------------------------------

    logger.info(
        "Routing decision: RETRIEVAL "
        f"(Iterative re-retrieval pass "
        f"{iteration_count + 1})"
    )

    return "retrieval"


# ============================================================
# BUILD LANGGRAPH
# ============================================================


def build_verification_graph(
    hybrid_retriever: Optional[
        HybridRetriever
    ] = None,
):
    """
    Construct and compile the LangGraph verification workflow.

    The graph contains:

        retrieval
            ↓
        verification
            ↓
        ┌───────────────┐
        │               │
        ↓               ↓
    retrieval          END
    """

    # --------------------------------------------------------
    # Create nodes
    # --------------------------------------------------------

    retrieval_node = RetrievalAgentNode(
        hybrid_retriever=hybrid_retriever
    )

    verification_node = VerificationAgentNode()

    # --------------------------------------------------------
    # Create StateGraph
    # --------------------------------------------------------

    workflow = StateGraph(
        VerificationAgentState
    )

    # --------------------------------------------------------
    # Add nodes
    # --------------------------------------------------------

    workflow.add_node(
        "retrieval",
        retrieval_node,
    )

    workflow.add_node(
        "verification",
        verification_node,
    )

    # --------------------------------------------------------
    # Entry point
    # --------------------------------------------------------

    workflow.set_entry_point(
        "retrieval"
    )

    # --------------------------------------------------------
    # Retrieval -> Verification
    # --------------------------------------------------------

    workflow.add_edge(
        "retrieval",
        "verification",
    )

    # --------------------------------------------------------
    # Verification -> Retrieval / END
    # --------------------------------------------------------

    workflow.add_conditional_edges(
        "verification",
        should_continue,
        {
            "retrieval": "retrieval",
            END: END,
        },
    )

    # --------------------------------------------------------
    # Compile graph
    # --------------------------------------------------------

    compiled_app = workflow.compile()

    logger.info(
        "Successfully compiled LangGraph "
        "Verification Agent Workflow."
    )

    return compiled_app


# ============================================================
# RUN AGENTIC VERIFICATION
# ============================================================


def run_agentic_verification(
    user_query: str,
    max_iterations: int = 2,
    hybrid_retriever: Optional[
        HybridRetriever
    ] = None,
    doc_id: Optional[str] = None,
    course_id: Optional[str] = None,
) -> VerificationAgentState:
    """
    Execute the complete agentic verification workflow.

    Args:
        user_query:
            Student/user question.

        max_iterations:
            Maximum number of retrieval/verification
            iterations.

        hybrid_retriever:
            Optional HybridRetriever instance.

        doc_id:
            Specific uploaded document ID.

            When supplied, document-level retrieval
            takes priority over course-level retrieval.

        course_id:
            Course ID.

            Used when doc_id is not supplied.

    Returns:
        Final VerificationAgentState.
    """

    # ========================================================
    # VALIDATE QUERY
    # ========================================================

    if not user_query or not user_query.strip():

        raise ValueError(
            "user_query cannot be empty."
        )

    # ========================================================
    # NORMALIZE SCOPE
    # ========================================================

    normalized_doc_id = (
        str(doc_id).strip()
        if doc_id is not None
        else None
    )

    normalized_course_id = (
        str(course_id).strip()
        if course_id is not None
        else None
    )

    # Empty strings should become None.

    if not normalized_doc_id:
        normalized_doc_id = None

    if not normalized_course_id:
        normalized_course_id = None

    # ========================================================
    # LOG RETRIEVAL SCOPE
    # ========================================================

    if normalized_doc_id:

        logger.info(
            "Starting verification workflow with "
            f"DOCUMENT scope: doc_id="
            f"{normalized_doc_id}"
        )

    elif normalized_course_id:

        logger.info(
            "Starting verification workflow with "
            f"COURSE scope: course_id="
            f"{normalized_course_id}"
        )

    else:

        logger.warning(
            "Starting verification workflow without "
            "doc_id or course_id. "
            "Retrieval will be unscoped."
        )

    # ========================================================
    # VALIDATE ITERATION LIMIT
    # ========================================================

    if max_iterations < 1:

        max_iterations = 1

    # ========================================================
    # BUILD GRAPH
    # ========================================================

    graph = build_verification_graph(
        hybrid_retriever=hybrid_retriever
    )

    # ========================================================
    # INITIAL STATE
    # ========================================================

    initial_state: VerificationAgentState = {

        # ----------------------------------------------------
        # Query
        # ----------------------------------------------------

        "user_query": user_query.strip(),

        # ----------------------------------------------------
        # Retrieval scope
        # ----------------------------------------------------

        "course_id": normalized_course_id,

        "doc_id": normalized_doc_id,

        # ----------------------------------------------------
        # Query concepts
        # ----------------------------------------------------

        "extracted_query_concepts": [],

        # ----------------------------------------------------
        # Evidence repositories
        # ----------------------------------------------------

        "retrieved_chunks": [],

        "retrieved_hyperedges": [],

        "retrieved_concepts": [],

        "sources": [],

        # ----------------------------------------------------
        # Retrieval summary
        # ----------------------------------------------------

        "retrieval_summary": {},

        # ----------------------------------------------------
        # Verification outputs
        # ----------------------------------------------------

        "is_sufficient": False,

        "verification_reasoning": "",

        "relevance_score": 0.0,

        "missing_concepts": [],

        "confidence": 0.0,

        # ----------------------------------------------------
        # Generation outputs
        # ----------------------------------------------------

        "final_answer": "",

        "verification_result": "",

        "unsupported_claims": [],

        # ----------------------------------------------------
        # Execution control
        # ----------------------------------------------------

        "iteration_count": 0,

        "max_iterations": max_iterations,

        # ----------------------------------------------------
        # Initial status
        # ----------------------------------------------------

        "status": "INITIALIZED",
    }

    # ========================================================
    # EXECUTE GRAPH
    # ========================================================

    logger.info(
        "Invoking agentic verification graph..."
    )

    final_state = graph.invoke(
        initial_state
    )

    # ========================================================
    # ENSURE SCOPE IS PRESERVED
    # ========================================================

    if normalized_doc_id is not None:

        final_state["doc_id"] = (
            normalized_doc_id
        )

    if normalized_course_id is not None:

        final_state["course_id"] = (
            normalized_course_id
        )

    # ========================================================
    # FINAL LOG
    # ========================================================

    logger.info(
        "Agentic verification workflow completed. "
        f"status={final_state.get('status')}, "
        f"iterations="
        f"{final_state.get('iteration_count', 0)}, "
        f"doc_id="
        f"{final_state.get('doc_id')}, "
        f"course_id="
        f"{final_state.get('course_id')}"
    )

    return final_state