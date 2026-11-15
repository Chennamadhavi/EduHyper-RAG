"""
Hypergraph Retriever for EduHyperRAG.

Performs:
1. Query-term extraction
2. Concept matching
3. Hyperedge matching
4. 1-hop concept diffusion
5. Source-chunk collection

The retriever is document-scoped when a hypergraph JSON path
is explicitly provided. It never intentionally falls back to
a global hypergraph during retrieval.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field

from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine
from src.utils.logger import get_logger


logger = get_logger("hypergraph_retriever")


# =============================================================
# RESULT MODELS
# =============================================================


class RetrievedConcept(BaseModel):
    """Schema for a retrieved concept node."""

    concept_id: str
    name: str
    entity_type: str
    description: str

    source_chunk_ids: List[str] = Field(
        default_factory=list
    )

    retrieval_method: str = "hypergraph"


class RetrievedHyperedge(BaseModel):
    """Schema for a retrieved hyperedge."""

    hyperedge_id: str
    label: str
    cardinality: int
    concepts: List[str]
    description: str

    source_chunk_ids: List[str] = Field(
        default_factory=list
    )

    retrieval_method: str = "hypergraph"


class HypergraphRetrievalResult(BaseModel):
    """Result schema for hypergraph retrieval."""

    query: str

    matched_query_terms: List[str] = Field(
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

    retrieval_method: str = "hypergraph"


# =============================================================
# HYPERGRAPH RETRIEVER
# =============================================================


class HypergraphRetriever:
    """
    Hypergraph-driven retrieval engine.

    A hypergraph must be explicitly supplied for retrieval.

    This prevents accidental retrieval from an old global
    hypergraph containing unrelated documents.
    """

    def __init__(
        self,
        hypergraph_json_path: Optional[
            Union[str, Path]
        ] = None,
    ):
        self.hypergraph_json_path = (
            Path(hypergraph_json_path)
            if hypergraph_json_path
            else None
        )

        self.query_engine: Optional[
            EduHypergraphQueryEngine
        ] = None

        if self.hypergraph_json_path is not None:

            if self.hypergraph_json_path.exists():

                self.query_engine = (
                    EduHypergraphQueryEngine(
                        self.hypergraph_json_path
                    )
                )

                logger.info(
                    "Initialized hypergraph retriever "
                    f"with: {self.hypergraph_json_path}"
                )

            else:

                logger.warning(
                    "Specified hypergraph does not exist: "
                    f"{self.hypergraph_json_path}"
                )

    # =========================================================
    # SEARCH
    # =========================================================

    def search(
        self,
        query: str,
        max_hyperedges: int = 5,
        hypergraph_json_path: Optional[
            Union[str, Path]
        ] = None,
    ) -> HypergraphRetrievalResult:
        """
        Execute hypergraph retrieval.

        Args:
            query:
                User's question.

            max_hyperedges:
                Maximum number of hyperedges to return.

            hypergraph_json_path:
                Explicit document-specific hypergraph path.

        Returns:
            HypergraphRetrievalResult.
        """

        # -----------------------------------------------------
        # Validate query
        # -----------------------------------------------------

        if not query or not query.strip():

            return HypergraphRetrievalResult(
                query="",
                matched_query_terms=[],
                concepts=[],
                hyperedges=[],
                sources=[],
            )

        # -----------------------------------------------------
        # Resolve hypergraph path
        # -----------------------------------------------------

        resolved_path: Optional[Path] = None

        if hypergraph_json_path is not None:

            resolved_path = Path(
                hypergraph_json_path
            )

        elif self.hypergraph_json_path is not None:

            resolved_path = self.hypergraph_json_path

        # -----------------------------------------------------
        # Never use an implicit global hypergraph
        # -----------------------------------------------------

        if resolved_path is None:

            logger.warning(
                "Hypergraph retrieval skipped because "
                "no explicit hypergraph path was supplied."
            )

            return HypergraphRetrievalResult(
                query=query,
                matched_query_terms=self._extract_query_terms(
                    query
                ),
                concepts=[],
                hyperedges=[],
                sources=[],
            )

        # -----------------------------------------------------
        # Validate hypergraph file
        # -----------------------------------------------------

        if not resolved_path.exists():

            logger.warning(
                "Hypergraph retrieval skipped because "
                f"file does not exist: {resolved_path}"
            )

            return HypergraphRetrievalResult(
                query=query,
                matched_query_terms=self._extract_query_terms(
                    query
                ),
                concepts=[],
                hyperedges=[],
                sources=[],
            )

        # -----------------------------------------------------
        # Load requested hypergraph
        # -----------------------------------------------------

        try:

            query_engine = (
                EduHypergraphQueryEngine(
                    resolved_path
                )
            )

        except Exception as exc:

            logger.exception(
                "Failed to load hypergraph "
                f"{resolved_path}: {exc}"
            )

            return HypergraphRetrievalResult(
                query=query,
                matched_query_terms=self._extract_query_terms(
                    query
                ),
                concepts=[],
                hyperedges=[],
                sources=[],
            )

        # -----------------------------------------------------
        # Extract query terms
        # -----------------------------------------------------

        query_terms = self._extract_query_terms(
            query
        )

        matched_concepts: Dict[
            str, RetrievedConcept
        ] = {}

        matched_hyperedges: Dict[
            str, RetrievedHyperedge
        ] = {}

        source_chunk_ids: Set[str] = set()

        # =====================================================
        # 1. CONCEPT MATCHING
        # =====================================================

        for concept_id, concept in (
            query_engine.concepts.items()
        ):

            name = str(
                concept.get("name", "")
            )

            description = str(
                concept.get(
                    "description",
                    ""
                )
            )

            name_lower = name.lower()
            description_lower = (
                description.lower()
            )

            # Match query terms against concept
            # name or description.
            is_match = any(
                term in name_lower
                or term in description_lower
                for term in query_terms
            )

            if not is_match:
                continue

            concept_obj = RetrievedConcept(
                concept_id=str(
                    concept.get(
                        "concept_id",
                        concept_id
                    )
                ),

                name=name,

                entity_type=str(
                    concept.get(
                        "entity_type",
                        "Concept"
                    )
                ),

                description=description,

                source_chunk_ids=[
                    str(x)
                    for x in concept.get(
                        "source_chunk_ids",
                        []
                    )
                ],

                retrieval_method="hypergraph",
            )

            matched_concepts[
                name.lower()
            ] = concept_obj

            source_chunk_ids.update(
                concept_obj.source_chunk_ids
            )

        # =====================================================
        # 2. HYPEREDGE MATCHING
        # =====================================================

        for hyperedge_id, edge in (
            query_engine.hyperedges.items()
        ):

            label = str(
                edge.get(
                    "label",
                    ""
                )
            )

            description = str(
                edge.get(
                    "description",
                    ""
                )
            )

            concepts = edge.get(
                "concepts",
                []
            )

            if not isinstance(
                concepts,
                list
            ):
                concepts = []

            member_names = [
                str(member).lower()
                for member in concepts
            ]

            # Check whether the hyperedge contains
            # a matched concept.
            has_matched_concept = any(
                member_name in matched_concepts
                for member_name in member_names
            )

            # Check whether the hyperedge text
            # matches the query.
            has_query_term = any(
                term in label.lower()
                or term in description.lower()
                for term in query_terms
            )

            if not (
                has_matched_concept
                or has_query_term
            ):
                continue

            edge_obj = RetrievedHyperedge(
                hyperedge_id=str(
                    edge.get(
                        "hyperedge_id",
                        hyperedge_id
                    )
                ),

                label=label,

                cardinality=len(
                    concepts
                ),

                concepts=[
                    str(member)
                    for member in concepts
                ],

                description=description,

                source_chunk_ids=[
                    str(x)
                    for x in edge.get(
                        "source_chunk_ids",
                        []
                    )
                ],

                retrieval_method="hypergraph",
            )

            matched_hyperedges[
                str(hyperedge_id)
            ] = edge_obj

            source_chunk_ids.update(
                edge_obj.source_chunk_ids
            )

            # =================================================
            # 3. 1-HOP DIFFUSION
            # =================================================

            for member_name in concepts:

                member_key = str(
                    member_name
                ).lower()

                if member_key in matched_concepts:
                    continue

                node_data = (
                    query_engine.concepts.get(
                        member_name
                    )
                )

                if node_data is None:
                    continue

                diffused_concept = (
                    RetrievedConcept(
                        concept_id=str(
                            node_data.get(
                                "concept_id",
                                member_name
                            )
                        ),

                        name=str(
                            node_data.get(
                                "name",
                                member_name
                            )
                        ),

                        entity_type=str(
                            node_data.get(
                                "entity_type",
                                "Concept"
                            )
                        ),

                        description=str(
                            node_data.get(
                                "description",
                                ""
                            )
                        ),

                        source_chunk_ids=[
                            str(x)
                            for x in node_data.get(
                                "source_chunk_ids",
                                []
                            )
                        ],

                        retrieval_method=(
                            "hypergraph_diffused"
                        ),
                    )
                )

                matched_concepts[
                    member_key
                ] = diffused_concept

                source_chunk_ids.update(
                    diffused_concept.source_chunk_ids
                )

        # =====================================================
        # 4. RANK / TRUNCATE HYPEREDGES
        # =====================================================

        sorted_hyperedges = sorted(
            matched_hyperedges.values(),
            key=lambda edge: (
                edge.cardinality,
                len(
                    edge.source_chunk_ids
                ),
            ),
            reverse=True,
        )[:max_hyperedges]

        # =====================================================
        # 5. LOG
        # =====================================================

        logger.info(
            "Hypergraph search completed: "
            f"query='{query}', "
            f"concepts={len(matched_concepts)}, "
            f"hyperedges={len(sorted_hyperedges)}, "
            f"sources={len(source_chunk_ids)}, "
            f"hypergraph='{resolved_path}'"
        )

        # =====================================================
        # 6. RETURN
        # =====================================================

        return HypergraphRetrievalResult(
            query=query,

            matched_query_terms=query_terms,

            concepts=list(
                matched_concepts.values()
            ),

            hyperedges=sorted_hyperedges,

            sources=sorted(
                list(source_chunk_ids)
            ),

            retrieval_method="hypergraph",
        )

    # =========================================================
    # QUERY TERM EXTRACTION
    # =========================================================

    def _extract_query_terms(
        self,
        query: str,
    ) -> List[str]:
        """
        Extract meaningful keywords and bigrams
        from the user's query.

        This logic is domain-independent.
        """

        stop_words = {
            "what",
            "is",
            "the",
            "role",
            "of",
            "how",
            "does",
            "do",
            "in",
            "and",
            "to",
            "are",
            "connected",
            "participate",
            "production",
            "explain",
            "describe",
            "a",
            "an",
            "with",
            "for",
            "on",
            "by",
            "from",
            "at",
            "why",
            "where",
            "when",
            "which",
            "can",
            "could",
            "would",
            "should",
            "please",
            "give",
            "me",
            "about",
        }

        tokens = re.findall(
            r"\b\w+\b",
            query.lower()
        )

        meaningful_tokens = [
            token
            for token in tokens
            if (
                token not in stop_words
                and len(token) > 2
            )
        ]

        # -----------------------------------------------------
        # Bigrams
        # -----------------------------------------------------

        meaningful_bigrams: List[str] = []

        for index in range(
            len(tokens) - 1
        ):

            first = tokens[index]
            second = tokens[index + 1]

            if (
                first in stop_words
                or second in stop_words
            ):
                continue

            if (
                len(first) <= 2
                or len(second) <= 2
            ):
                continue

            meaningful_bigrams.append(
                f"{first} {second}"
            )

        # -----------------------------------------------------
        # Preserve order while removing duplicates
        # -----------------------------------------------------

        terms: List[str] = []

        seen: Set[str] = set()

        for term in (
            meaningful_tokens
            + meaningful_bigrams
        ):

            if term not in seen:

                seen.add(term)
                terms.append(term)

        return terms