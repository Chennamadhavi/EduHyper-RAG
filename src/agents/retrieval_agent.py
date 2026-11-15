"""
Retrieval Agent Node for LangGraph Workflow.

Handles:
1. Initial hybrid retrieval
2. Targeted re-retrieval using missing concepts
3. Document-level retrieval isolation
4. Course-level retrieval isolation
5. Evidence accumulation across verification iterations
6. Strict scope propagation to the hybrid retriever
"""

from typing import Dict, List, Set

from src.agents.state import VerificationAgentState
from src.retrieval.hybrid_retriever import HybridRetriever
from src.utils.logger import get_logger


logger = get_logger("retrieval_agent")


class RetrievalAgentNode:
    """
    LangGraph node executing initial and iterative evidence retrieval.

    Retrieval scope:

    - If doc_id is available, retrieval is restricted to that document.
    - Otherwise, if course_id is available, retrieval is restricted
      to that course.
    - If neither is available, a warning is generated because
      retrieval is unscoped.
    """

    def __init__(
        self,
        hybrid_retriever: HybridRetriever = None,
    ):
        self.hybrid_retriever = (
            hybrid_retriever
            or HybridRetriever()
        )

    # =========================================================
    # MAIN NODE
    # =========================================================

    def __call__(
        self,
        state: VerificationAgentState,
    ) -> VerificationAgentState:
        """
        Execute one retrieval pass and update workflow state.
        """

        # =====================================================
        # 1. READ STATE
        # =====================================================

        query = state.get(
            "user_query",
            "",
        )

        iteration = state.get(
            "iteration_count",
            0,
        )

        missing = state.get(
            "missing_concepts",
            [],
        )

        # -----------------------------------------------------
        # Document/course context
        # -----------------------------------------------------

        doc_id = state.get(
            "doc_id"
        )

        course_id = state.get(
            "course_id"
        )

        # Normalize IDs
        if doc_id is not None:
            doc_id = str(doc_id).strip() or None

        if course_id is not None:
            course_id = str(course_id).strip() or None

        logger.info(
            "Retrieval context: "
            f"doc_id={doc_id}, "
            f"course_id={course_id}"
        )

        # -----------------------------------------------------
        # Scope validation
        # -----------------------------------------------------

        if not doc_id and not course_id:

            logger.warning(
                "RetrievalAgent received neither "
                "doc_id nor course_id. "
                "Semantic retrieval may be unscoped and "
                "hypergraph retrieval will be disabled."
            )

        elif doc_id:

            logger.info(
                f"Using DOCUMENT scope for retrieval: "
                f"doc_id={doc_id}"
            )

        else:

            logger.info(
                f"Using COURSE scope for retrieval: "
                f"course_id={course_id}"
            )

        # =====================================================
        # 2. VALIDATE USER QUERY
        # =====================================================

        if not query or not query.strip():

            logger.warning(
                "RetrievalAgent received an empty query."
            )

            new_state = dict(state)

            new_state["retrieved_chunks"] = (
                state.get(
                    "retrieved_chunks",
                    [],
                )
            )

            new_state["retrieved_hyperedges"] = (
                state.get(
                    "retrieved_hyperedges",
                    [],
                )
            )

            new_state["retrieved_concepts"] = (
                state.get(
                    "retrieved_concepts",
                    [],
                )
            )

            new_state["sources"] = (
                state.get(
                    "sources",
                    [],
                )
            )

            new_state["status"] = "RETRIEVAL_EMPTY"

            return new_state

        # =====================================================
        # 3. BUILD EFFECTIVE SEARCH QUERY
        # =====================================================

        if (
            iteration == 0
            or not missing
        ):

            search_query = query

            logger.info(
                "Initial Retrieval Pass "
                f"(Iteration {iteration}) "
                f"for query: '{search_query}'"
            )

        else:

            # Only use a small number of missing concepts.
            #
            # This prevents uncontrolled query expansion.
            expanded_terms = " ".join(
                str(term)
                for term in missing[:3]
                if term
            )

            if expanded_terms:

                search_query = (
                    f"{query} "
                    f"{expanded_terms}"
                )

            else:

                search_query = query

            logger.info(
                "Targeted Re-Retrieval Pass "
                f"(Iteration {iteration}) "
                f"with expanded terms: "
                f"'{expanded_terms}'"
            )

        # =====================================================
        # 4. EXECUTE DOCUMENT/COURSE-AWARE RETRIEVAL
        # =====================================================

        try:

            retrieval_out = (
                self.hybrid_retriever.retrieve(
                    query=search_query,

                    top_k_semantic=3,

                    top_k_hyperedges=4,

                    # -------------------------------------------------
                    # IMPORTANT:
                    # Document scope takes priority over course scope.
                    # -------------------------------------------------

                    doc_id=doc_id,

                    course_id=course_id,
                )
            )

        except Exception as exc:

            logger.exception(
                "Hybrid retrieval failed: "
                f"{exc}"
            )

            new_state = dict(state)

            new_state["status"] = (
                "RETRIEVAL_ERROR"
            )

            new_state["retrieval_error"] = str(
                exc
            )

            return new_state

        # =====================================================
        # 5. READ EXISTING EVIDENCE
        # =====================================================

        existing_chunks = state.get(
            "retrieved_chunks",
            [],
        )

        existing_hyperedges = state.get(
            "retrieved_hyperedges",
            [],
        )

        existing_concepts = state.get(
            "retrieved_concepts",
            [],
        )

        existing_sources = set(
            state.get(
                "sources",
                [],
            )
        )

        # =====================================================
        # 6. DEDUPLICATE SEMANTIC CHUNKS
        # =====================================================

        chunk_map = {
            chunk.get("chunk_id"): chunk
            for chunk in existing_chunks
            if chunk.get("chunk_id")
        }

        for new_chunk in retrieval_out.get(
            "chunks",
            [],
        ):

            chunk_id = new_chunk.get(
                "chunk_id"
            )

            if not chunk_id:
                continue

            chunk_map[
                chunk_id
            ] = new_chunk

            existing_sources.add(
                chunk_id
            )

        # =====================================================
        # 7. DEDUPLICATE HYPEREDGES
        # =====================================================

        edge_map = {
            edge.get("hyperedge_id"): edge
            for edge in existing_hyperedges
            if edge.get("hyperedge_id")
        }

        for new_edge in retrieval_out.get(
            "hyperedges",
            [],
        ):

            edge_id = new_edge.get(
                "hyperedge_id"
            )

            if not edge_id:
                continue

            edge_map[
                edge_id
            ] = new_edge

            existing_sources.update(
                new_edge.get(
                    "source_chunk_ids",
                    [],
                )
            )

        # =====================================================
        # 8. DEDUPLICATE CONCEPTS
        # =====================================================

        concept_map = {
            concept.get("name", "").lower(): concept
            for concept in existing_concepts
            if concept.get("name")
        }

        for new_concept in retrieval_out.get(
            "concepts",
            [],
        ):

            concept_name = str(
                new_concept.get(
                    "name",
                    "",
                )
            ).strip()

            if not concept_name:
                continue

            concept_map[
                concept_name.lower()
            ] = new_concept

            existing_sources.update(
                new_concept.get(
                    "source_chunk_ids",
                    [],
                )
            )

        # =====================================================
        # 9. UPDATE STATE
        # =====================================================

        new_state = dict(
            state
        )

        new_state[
            "retrieved_chunks"
        ] = list(
            chunk_map.values()
        )

        new_state[
            "retrieved_hyperedges"
        ] = list(
            edge_map.values()
        )

        new_state[
            "retrieved_concepts"
        ] = list(
            concept_map.values()
        )

        new_state[
            "sources"
        ] = sorted(
            list(
                existing_sources
            )
        )

        new_state[
            "iteration_count"
        ] = iteration + 1

        new_state[
            "status"
        ] = "RETRIEVED"

        # Preserve scope explicitly in state.
        new_state[
            "doc_id"
        ] = doc_id

        new_state[
            "course_id"
        ] = course_id

        # =====================================================
        # 10. STORE RETRIEVAL SUMMARY
        # =====================================================

        retrieval_summary = (
            retrieval_out.get(
                "retrieval_summary",
                {},
            )
        )

        new_state[
            "retrieval_summary"
        ] = retrieval_summary

        # =====================================================
        # 11. LOG RESULTS
        # =====================================================

        logger.info(
            "Retrieval pass "
            f"{iteration + 1} complete. "
            f"New chunks="
            f"{len(retrieval_out.get('chunks', []))}, "
            f"new concepts="
            f"{len(retrieval_out.get('concepts', []))}, "
            f"new hyperedges="
            f"{len(retrieval_out.get('hyperedges', []))}. "
            f"Total accumulated evidence="
            f"{len(new_state['retrieved_chunks'])} "
            f"chunk(s), "
            f"{len(new_state['retrieved_concepts'])} "
            f"concept(s), "
            f"{len(new_state['retrieved_hyperedges'])} "
            f"hyperedge(s)."
        )

        return new_state