"""
Hybrid Retriever for EduHyperRAG.

Combines:
1. Semantic vector retrieval using ChromaDB
2. Hypergraph retrieval using HyperNetX

Retrieval isolation:
- Document-level retrieval is the strongest scope.
- Course-level semantic retrieval is supported.
- A global hypergraph is NEVER used as a fallback for a
  course-scoped retrieval.
- The production student workflow should provide doc_id.
"""

from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field

from src.config import config
from src.retrieval.hypergraph_retriever import (
    HypergraphRetriever,
    RetrievedConcept,
    RetrievedHyperedge,
)
from src.retrieval.semantic_retriever import (
    SemanticChunkResult,
    SemanticRetriever,
)
from src.utils.logger import get_logger


logger = get_logger("hybrid_retriever")


class HybridRetrievalResult(BaseModel):
    """Unified hybrid retrieval output schema."""

    query: str

    chunks: List[
        SemanticChunkResult
    ] = Field(
        default_factory=list
    )

    concepts: List[
        RetrievedConcept
    ] = Field(
        default_factory=list
    )

    hyperedges: List[
        RetrievedHyperedge
    ] = Field(
        default_factory=list
    )

    sources: List[str] = Field(
        default_factory=list
    )

    retrieval_summary: Dict[
        str, Any
    ] = Field(
        default_factory=dict
    )


class HybridRetriever:
    """
    Orchestrates combined semantic and hypergraph retrieval.

    Retrieval scopes:

    1. doc_id supplied:
       - Semantic retrieval restricted to document.
       - Hypergraph restricted to document-specific graph.

    2. course_id supplied without doc_id:
       - Semantic retrieval restricted to course.
       - Global hypergraph is NOT used.

    3. Neither supplied:
       - Unrestricted semantic retrieval.
       - Global hypergraph may be used for legacy/evaluation
         workflows only.
    """

    def __init__(
        self,
        semantic_retriever: Optional[
            SemanticRetriever
        ] = None,
        hypergraph_retriever: Optional[
            HypergraphRetriever
        ] = None,
    ):

        self.semantic_retriever = (
            semantic_retriever
            or SemanticRetriever()
        )

        self.hypergraph_retriever = (
            hypergraph_retriever
            or HypergraphRetriever()
        )

    # =========================================================
    # HYBRID RETRIEVAL
    # =========================================================

    def retrieve(
        self,
        query: str,
        top_k_semantic: int = 3,
        top_k_hyperedges: int = 5,
        doc_id: Optional[str] = None,
        course_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute hybrid retrieval.

        Args:
            query:
                User's question.

            top_k_semantic:
                Maximum number of semantic chunks.

            top_k_hyperedges:
                Maximum number of hyperedges.

            doc_id:
                Restrict retrieval to one uploaded document.

            course_id:
                Restrict semantic retrieval to one course
                when doc_id is not supplied.

        Returns:
            JSON-serializable hybrid retrieval result.
        """

        # =====================================================
        # 1. Validate query
        # =====================================================

        if not query or not query.strip():

            return {
                "query": "",
                "chunks": [],
                "concepts": [],
                "hyperedges": [],
                "sources": [],
                "retrieval_summary": {
                    "num_semantic_chunks": 0,
                    "num_concepts": 0,
                    "num_hyperedges": 0,
                    "num_sources": 0,
                    "doc_id": doc_id,
                    "course_id": course_id,
                },
            }

        logger.info(
            f"Executing hybrid retrieval for query "
            f"'{query}' "
            f"(doc_id={doc_id}, course_id={course_id})"
        )

        # =====================================================
        # 2. Build semantic retrieval filter
        # =====================================================

        where_filter: Optional[
            Dict[str, Any]
        ] = None

        if doc_id:

            # -------------------------------------------------
            # Strongest isolation:
            # specific document
            # -------------------------------------------------

            where_filter = {
                "doc_id": str(doc_id)
            }

            logger.info(
                f"Semantic retrieval restricted to "
                f"document: {doc_id}"
            )

        elif course_id:

            # -------------------------------------------------
            # Course-level isolation
            # -------------------------------------------------

            where_filter = {
                "course_id": str(course_id)
            }

            logger.info(
                f"Semantic retrieval restricted to "
                f"course: {course_id}"
            )

        else:

            logger.warning(
                "Hybrid retrieval running without "
                "document or course scope."
            )

        # =====================================================
        # 3. Determine hypergraph file
        # =====================================================

        hypergraph_path: Optional[Any] = None

        if doc_id:

            # -------------------------------------------------
            # Document-specific hypergraph
            # -------------------------------------------------

            document_hypergraph = (
                config.knowledge_base_dir
                / f"hypergraph_{doc_id}.json"
            )

            if document_hypergraph.exists():

                hypergraph_path = (
                    document_hypergraph
                )

                logger.info(
                    f"Using document-specific "
                    f"hypergraph: "
                    f"{document_hypergraph}"
                )

            else:

                # IMPORTANT:
                # Do NOT fall back to global hypergraph.json.
                #
                # Falling back would allow evidence from
                # another document to enter the answer.

                logger.warning(
                    f"Document-specific hypergraph "
                    f"not found for doc_id='{doc_id}'. "
                    f"Hypergraph retrieval will be skipped."
                )

        elif course_id:

            # -------------------------------------------------
            # Course-scoped retrieval without a specific
            # document.
            #
            # We currently have document-level hypergraphs,
            # not a course-level aggregated hypergraph.
            #
            # Therefore NEVER use global hypergraph.json here.
            # -------------------------------------------------

            logger.info(
                f"Course-scoped retrieval requested for "
                f"course_id='{course_id}' without doc_id. "
                f"Skipping hypergraph retrieval to prevent "
                f"cross-document contamination."
            )

            hypergraph_path = None

        else:

            # -------------------------------------------------
            # Legacy/unrestricted mode.
            #
            # This is retained for evaluation scripts and
            # development workflows that intentionally operate
            # on the global knowledge base.
            # -------------------------------------------------

            global_hypergraph = (
                config.knowledge_base_dir
                / "hypergraph.json"
            )

            if global_hypergraph.exists():

                hypergraph_path = (
                    global_hypergraph
                )

                logger.warning(
                    "Using global hypergraph because "
                    "no document/course scope was supplied."
                )

        # =====================================================
        # 4. Semantic retrieval
        # =====================================================

        semantic_chunks = (
            self.semantic_retriever.search(
                query=query,
                top_k=top_k_semantic,
                where_filter=where_filter,
            )
        )

        # =====================================================
        # 5. Hypergraph retrieval
        # =====================================================

        if hypergraph_path is not None:

            hyper_result = (
                self.hypergraph_retriever.search(
                    query=query,
                    max_hyperedges=top_k_hyperedges,
                    hypergraph_json_path=hypergraph_path,
                )
            )

        else:

            # No safe hypergraph available for the current
            # retrieval scope.

            hyper_result = type(
                "EmptyHypergraphResult",
                (),
                {
                    "concepts": [],
                    "hyperedges": [],
                    "sources": [],
                },
            )()

        # =====================================================
        # 6. Combine source chunk IDs
        # =====================================================

        all_sources: Set[str] = set(
            hyper_result.sources
        )

        for semantic_chunk in semantic_chunks:

            all_sources.add(
                semantic_chunk.chunk_id
            )

        # =====================================================
        # 7. Build unified result
        # =====================================================

        result_obj = HybridRetrievalResult(

            query=query,

            chunks=semantic_chunks,

            concepts=(
                hyper_result.concepts
            ),

            hyperedges=(
                hyper_result.hyperedges
            ),

            sources=sorted(
                list(all_sources)
            ),

            retrieval_summary={

                "num_semantic_chunks": len(
                    semantic_chunks
                ),

                "num_concepts": len(
                    hyper_result.concepts
                ),

                "num_hyperedges": len(
                    hyper_result.hyperedges
                ),

                "num_sources": len(
                    all_sources
                ),

                "doc_id": doc_id,

                "course_id": course_id,

                "semantic_filter": (
                    where_filter
                ),

                "hypergraph_path": (
                    str(hypergraph_path)
                    if hypergraph_path
                    else None
                ),
            },
        )

        # =====================================================
        # 8. Logging
        # =====================================================

        logger.info(
            f"Hybrid retrieval completed: "
            f"{len(semantic_chunks)} semantic chunks, "
            f"{len(hyper_result.concepts)} concepts, "
            f"{len(hyper_result.hyperedges)} hyperedges."
        )

        return result_obj.model_dump()