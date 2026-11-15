"""
Hybrid Retriever for EduHyperRAG.

Combines:
1. Semantic vector retrieval using ChromaDB
2. Hypergraph retrieval using HyperNetX

Supports strict document-level and course-level isolation.
Production retrieval should always provide either doc_id or course_id.
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

    chunks: List[SemanticChunkResult] = Field(
        default_factory=list
    )

    concepts: List[RetrievedConcept] = Field(
        default_factory=list
    )

    hyperedges: List[RetrievedHyperedge] = Field(
        default_factory=list
    )

    sources: List[str] = Field(
        default_factory=list
    )

    retrieval_summary: Dict[str, Any] = Field(
        default_factory=dict
    )


class HybridRetriever:
    """
    Orchestrates semantic and hypergraph retrieval.

    Isolation rules:

    1. If doc_id is provided:
       - Semantic retrieval is restricted to that document.
       - Hypergraph retrieval uses only hypergraph_<doc_id>.json.

    2. If course_id is provided without doc_id:
       - Semantic retrieval is restricted to that course.
       - Hypergraph retrieval is skipped because a single global
         hypergraph cannot safely represent course-level isolation.

    3. If neither is provided:
       - Retrieval is treated as unscoped/legacy retrieval.
       - Hypergraph retrieval is NOT performed.
    """

    def __init__(
        self,
        semantic_retriever: Optional[SemanticRetriever] = None,
        hypergraph_retriever: Optional[HypergraphRetriever] = None,
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
                Number of semantic chunks to retrieve.

            top_k_hyperedges:
                Maximum number of hyperedges to retrieve.

            doc_id:
                Restrict retrieval to one document.

            course_id:
                Restrict semantic retrieval to one course
                when doc_id is not supplied.

        Returns:
            JSON-serializable hybrid retrieval result.
        """

        # -----------------------------------------------------
        # Validate query
        # -----------------------------------------------------

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

        # -----------------------------------------------------
        # Normalize scope
        # -----------------------------------------------------

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

        logger.info(
            "Executing hybrid retrieval: "
            f"query='{query}', "
            f"doc_id={normalized_doc_id}, "
            f"course_id={normalized_course_id}"
        )

        # =====================================================
        # 1. BUILD SEMANTIC RETRIEVAL FILTER
        # =====================================================

        where_filter: Optional[Dict[str, Any]] = None

        if normalized_doc_id:

            # Document-level isolation has highest priority.
            where_filter = {
                "doc_id": normalized_doc_id
            }

        elif normalized_course_id:

            # Course-level isolation.
            where_filter = {
                "course_id": normalized_course_id
            }

        # =====================================================
        # 2. DETERMINE HYPERGRAPH SCOPE
        # =====================================================

        hypergraph_path: Optional[Any] = None

        if normalized_doc_id:

            document_hypergraph = (
                config.knowledge_base_dir
                / f"hypergraph_{normalized_doc_id}.json"
            )

            if document_hypergraph.exists():

                hypergraph_path = document_hypergraph

                logger.info(
                    "Using document-specific hypergraph: "
                    f"{document_hypergraph}"
                )

            else:

                # IMPORTANT:
                # Never fall back to global hypergraph.json.
                logger.warning(
                    "Document-specific hypergraph not found "
                    f"for doc_id='{normalized_doc_id}': "
                    f"{document_hypergraph}"
                )

        elif normalized_course_id:

            # We currently store hypergraphs per document.
            #
            # Therefore, using a global hypergraph here could
            # mix documents from different courses.
            #
            # Semantic retrieval is still safely restricted
            # to the selected course.
            logger.info(
                "Course-level retrieval requested. "
                "Skipping hypergraph retrieval because no "
                "course-scoped hypergraph exists."
            )

        else:

            # No scope supplied.
            #
            # Do NOT load the legacy global hypergraph.
            logger.warning(
                "Unscoped retrieval requested. "
                "Semantic retrieval may be unrestricted, "
                "but hypergraph retrieval is disabled."
            )

        # =====================================================
        # 3. SEMANTIC RETRIEVAL
        # =====================================================

        semantic_chunks = (
            self.semantic_retriever.search(
                query=query,
                top_k=top_k_semantic,
                where_filter=where_filter,
            )
        )

        # =====================================================
        # 4. HYPERGRAPH RETRIEVAL
        # =====================================================

        concepts: List[RetrievedConcept] = []
        hyperedges: List[RetrievedHyperedge] = []
        hyper_sources: Set[str] = set()

        # Only perform hypergraph retrieval when a
        # document-specific hypergraph was found.
        if hypergraph_path is not None:

            hyper_result = (
                self.hypergraph_retriever.search(
                    query=query,
                    max_hyperedges=top_k_hyperedges,
                    hypergraph_json_path=hypergraph_path,
                )
            )

            concepts = hyper_result.concepts
            hyperedges = hyper_result.hyperedges
            hyper_sources = set(
                hyper_result.sources
            )

        else:

            logger.info(
                "Hypergraph retrieval skipped because "
                "no safe document-specific hypergraph "
                "is available."
            )

        # =====================================================
        # 5. COMBINE SOURCE IDS
        # =====================================================

        all_sources: Set[str] = set(
            hyper_sources
        )

        for semantic_chunk in semantic_chunks:

            if semantic_chunk.chunk_id:
                all_sources.add(
                    semantic_chunk.chunk_id
                )

        # =====================================================
        # 6. BUILD UNIFIED RESULT
        # =====================================================

        result_obj = HybridRetrievalResult(
            query=query,

            chunks=semantic_chunks,

            concepts=concepts,

            hyperedges=hyperedges,

            sources=sorted(
                list(all_sources)
            ),

            retrieval_summary={
                "num_semantic_chunks": len(
                    semantic_chunks
                ),

                "num_concepts": len(
                    concepts
                ),

                "num_hyperedges": len(
                    hyperedges
                ),

                "num_sources": len(
                    all_sources
                ),

                "doc_id": normalized_doc_id,

                "course_id": normalized_course_id,

                "semantic_filter": where_filter,

                "hypergraph_path": (
                    str(hypergraph_path)
                    if hypergraph_path is not None
                    else None
                ),

                "hypergraph_enabled": (
                    hypergraph_path is not None
                ),
            },
        )

        # =====================================================
        # 7. LOG RESULT
        # =====================================================

        logger.info(
            "Hybrid retrieval completed: "
            f"{len(semantic_chunks)} semantic chunks, "
            f"{len(concepts)} concepts, "
            f"{len(hyperedges)} hyperedges."
        )

        return result_obj.model_dump()