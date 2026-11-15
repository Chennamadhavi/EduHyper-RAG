"""
Evidence Verification Agent Node for EduHyper-RAG.

Evaluates:
1. Query concept coverage
2. Retrieved evidence relevance
3. Evidence grounding
4. Hypergraph support
5. Missing concepts

The verifier is domain-independent and contains no
hard-coded subject-specific concepts or answers.
"""

import re
from typing import Any, Dict, List, Tuple

from src.agents.state import VerificationAgentState
from src.utils.logger import get_logger


logger = get_logger("verification_agent")


class VerificationAgentNode:
    """
    Evaluates whether retrieved evidence is sufficient
    to answer the user's question without unsupported claims.
    """

    # =========================================================
    # MAIN VERIFICATION NODE
    # =========================================================

    def __call__(
        self,
        state: VerificationAgentState,
    ) -> VerificationAgentState:
        """Execute one evidence verification pass."""

        query = state.get(
            "user_query",
            "",
        )

        chunks = state.get(
            "retrieved_chunks",
            [],
        )

        concepts = state.get(
            "retrieved_concepts",
            [],
        )

        hyperedges = state.get(
            "retrieved_hyperedges",
            [],
        )

        iteration = state.get(
            "iteration_count",
            1,
        )

        max_iter = state.get(
            "max_iterations",
            2,
        )

        logger.info(
            "Executing Verification Agent Pass "
            f"(Iteration {iteration}/{max_iter}) "
            f"for query: '{query}'"
        )

        # =====================================================
        # 1. ANALYZE QUERY
        # =====================================================

        query_keywords, core_concepts = (
            self._analyze_query(query)
        )

        # =====================================================
        # 2. CHECK CONCEPT COVERAGE
        # =====================================================

        found_concepts, missing_concepts = (
            self._check_concept_coverage(
                core_concepts=core_concepts,
                retrieved_concepts=concepts,
                retrieved_hyperedges=hyperedges,
                retrieved_chunks=chunks,
            )
        )

        # =====================================================
        # 3. EVALUATE EVIDENCE
        # =====================================================

        relevance_score, reasoning_lines = (
            self._evaluate_evidence(
                query=query,
                query_keywords=query_keywords,
                chunks=chunks,
                concepts=concepts,
                hyperedges=hyperedges,
            )
        )

        # =====================================================
        # 4. CALCULATE COVERAGE
        # =====================================================

        if core_concepts:

            coverage_ratio = (
                len(found_concepts)
                / len(core_concepts)
            )

        else:

            coverage_ratio = (
                1.0
                if self._keywords_present(
                    query_keywords,
                    chunks,
                    concepts,
                    hyperedges,
                )
                else 0.0
            )

        coverage_ratio = max(
            0.0,
            min(
                1.0,
                coverage_ratio,
            ),
        )

        # =====================================================
        # 5. CALCULATE CONFIDENCE
        # =====================================================

        confidence = round(
            min(
                1.0,
                (
                    relevance_score
                    + coverage_ratio
                ) / 2.0,
            ),
            2,
        )

        # =====================================================
        # 6. DETERMINE SUFFICIENCY
        # =====================================================

        has_evidence = bool(
            chunks
            or concepts
            or hyperedges
        )

        sufficient_relevance = (
            relevance_score >= 0.50
        )

        sufficient_coverage = (
            coverage_ratio >= 0.50
            or not core_concepts
        )

        is_sufficient = (
            has_evidence
            and sufficient_relevance
            and sufficient_coverage
        )

        # =====================================================
        # 7. UPDATE STATE
        # =====================================================

        new_state = dict(state)

        new_state[
            "extracted_query_concepts"
        ] = core_concepts

        new_state[
            "missing_concepts"
        ] = missing_concepts

        new_state[
            "relevance_score"
        ] = round(
            relevance_score,
            2,
        )

        new_state[
            "confidence"
        ] = confidence

        new_state[
            "verification_result"
        ] = (
            "SUFFICIENT"
            if is_sufficient
            else "INSUFFICIENT"
        )

        # =====================================================
        # 8. SUFFICIENT EVIDENCE
        # =====================================================

        if is_sufficient:

            new_state[
                "is_sufficient"
            ] = True

            new_state[
                "status"
            ] = "VERIFIED"

            new_state[
                "verification_reasoning"
            ] = (
                "Sufficient evidence verified. "
                f"Covered concepts: {found_concepts}. "
                f"Coverage: {coverage_ratio:.2f}. "
                f"Relevance: {relevance_score:.2f}. "
                f"Confidence: {confidence:.2f}. "
                "Retrieved evidence provides sufficient "
                "grounding for answer generation."
            )

            logger.info(
                "Verification Result: SUFFICIENT "
                f"(Confidence: {confidence:.2f}, "
                f"Coverage: {coverage_ratio:.2f}, "
                f"Relevance: {relevance_score:.2f})"
            )

        # =====================================================
        # 9. INSUFFICIENT EVIDENCE
        # =====================================================

        else:

            new_state[
                "is_sufficient"
            ] = False

            if iteration >= max_iter:

                new_state[
                    "status"
                ] = "MAX_ITERATIONS_REACHED"

                new_state[
                    "verification_reasoning"
                ] = (
                    "Insufficient evidence after the "
                    f"maximum of {max_iter} iteration(s). "
                    f"Missing concepts: {missing_concepts}. "
                    f"Coverage: {coverage_ratio:.2f}. "
                    f"Relevance: {relevance_score:.2f}. "
                    "The knowledge base does not contain "
                    "sufficient verified evidence to answer "
                    "the question reliably."
                )

                logger.warning(
                    "Verification Result: "
                    "INSUFFICIENT - Maximum iterations reached."
                )

            else:

                new_state[
                    "status"
                ] = "INSUFFICIENT"

                new_state[
                    "verification_reasoning"
                ] = (
                    f"Insufficient evidence on iteration "
                    f"{iteration}. "
                    f"Missing concepts: {missing_concepts}. "
                    f"Coverage: {coverage_ratio:.2f}. "
                    f"Relevance: {relevance_score:.2f}. "
                    "Targeted re-retrieval is required."
                )

                logger.info(
                    "Verification Result: "
                    "INSUFFICIENT - requesting "
                    f"additional retrieval for "
                    f"{missing_concepts}."
                )

        # =====================================================
        # 10. LOG REASONING
        # =====================================================

        for line in reasoning_lines:

            logger.debug(
                f"Evidence evaluation: {line}"
            )

        return new_state

    # =========================================================
    # QUERY ANALYSIS
    # =========================================================

    def _analyze_query(
        self,
        query: str,
    ) -> Tuple[List[str], List[str]]:
        """
        Extract general keywords and candidate concepts.

        Domain-independent.
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
            "mechanism",
            "contribute",
            "contribution",
            "work",
            "works",
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
            "define",
            "definition",
            "tell",
        }

        tokens = re.findall(
            r"\b\w+\b",
            query.lower(),
        )

        keywords = [
            token
            for token in tokens
            if (
                token not in stop_words
                and len(token) > 2
            )
        ]

        concepts: List[str] = []

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

            concepts.append(
                f"{first} {second}"
            )

        if not concepts:
            concepts = list(keywords)

        keywords = self._unique_preserve_order(
            keywords
        )

        concepts = self._unique_preserve_order(
            concepts
        )

        return keywords, concepts

    # =========================================================
    # CONCEPT COVERAGE
    # =========================================================

    def _check_concept_coverage(
        self,
        core_concepts: List[str],
        retrieved_concepts: List[Dict[str, Any]],
        retrieved_hyperedges: List[Dict[str, Any]],
        retrieved_chunks: List[Dict[str, Any]],
    ) -> Tuple[List[str], List[str]]:
        """Identify supported and missing query concepts."""

        evidence_parts: List[str] = []

        for concept in retrieved_concepts:

            evidence_parts.append(
                str(
                    concept.get(
                        "name",
                        "",
                    )
                )
            )

            evidence_parts.append(
                str(
                    concept.get(
                        "description",
                        "",
                    )
                )
            )

        for hyperedge in retrieved_hyperedges:

            label = str(
                hyperedge.get(
                    "label",
                    "",
                )
            )

            description = str(
                hyperedge.get(
                    "description",
                    "",
                )
            )

            members = hyperedge.get(
                "concepts",
                [],
            )

            if not isinstance(
                members,
                list,
            ):
                members = []

            evidence_parts.append(
                label
            )

            evidence_parts.append(
                " ".join(
                    str(member)
                    for member in members
                )
            )

            evidence_parts.append(
                description
            )

        for chunk in retrieved_chunks:

            evidence_parts.append(
                str(
                    chunk.get(
                        "content",
                        "",
                    )
                )
            )

        evidence_text = " ".join(
            evidence_parts
        ).lower()

        evidence_text = re.sub(
            r"\s+",
            " ",
            evidence_text,
        ).strip()

        found: List[str] = []
        missing: List[str] = []

        for concept in core_concepts:

            normalized = (
                concept.lower().strip()
            )

            if not normalized:
                continue

            if normalized in evidence_text:

                found.append(
                    concept
                )

                continue

            concept_words = [
                word
                for word in re.findall(
                    r"\b\w+\b",
                    normalized,
                )
                if len(word) > 2
            ]

            if (
                len(concept_words) >= 2
                and all(
                    word in evidence_text
                    for word in concept_words
                )
            ):

                found.append(
                    concept
                )

            else:

                missing.append(
                    concept
                )

        return (
            self._unique_preserve_order(
                found
            ),
            self._unique_preserve_order(
                missing
            ),
        )

    # =========================================================
    # EVIDENCE EVALUATION
    # =========================================================

    def _evaluate_evidence(
        self,
        query: str,
        query_keywords: List[str],
        chunks: List[Dict[str, Any]],
        concepts: List[Dict[str, Any]],
        hyperedges: List[Dict[str, Any]],
    ) -> Tuple[float, List[str]]:
        """Evaluate relevance and grounding support."""

        reasoning: List[str] = []

        if (
            not chunks
            and not concepts
            and not hyperedges
        ):

            return (
                0.0,
                [
                    "No evidence retrieved."
                ],
            )

        scores: List[float] = []

        # =====================================================
        # SEMANTIC CHUNK RELEVANCE
        # =====================================================

        if chunks:

            chunk_scores: List[float] = []

            for chunk in chunks:

                score = chunk.get(
                    "relevance_score",
                    chunk.get(
                        "score",
                        0.0,
                    ),
                )

                try:
                    score = float(score)
                except (
                    TypeError,
                    ValueError,
                ):
                    score = 0.0

                score = max(
                    0.0,
                    min(
                        1.0,
                        score,
                    ),
                )

                chunk_scores.append(
                    score
                )

            if chunk_scores:

                max_chunk_score = max(
                    chunk_scores
                )

                avg_chunk_score = (
                    sum(chunk_scores)
                    / len(chunk_scores)
                )

                semantic_score = (
                    0.70 * max_chunk_score
                    + 0.30 * avg_chunk_score
                )

                scores.append(
                    semantic_score
                )

                reasoning.append(
                    "Semantic evidence: "
                    f"max={max_chunk_score:.2f}, "
                    f"average={avg_chunk_score:.2f}"
                )

        # =====================================================
        # KEYWORD SUPPORT
        # =====================================================

        evidence_parts: List[str] = []

        for chunk in chunks:

            evidence_parts.append(
                str(
                    chunk.get(
                        "content",
                        "",
                    )
                )
            )

        for concept in concepts:

            evidence_parts.append(
                str(
                    concept.get(
                        "name",
                        "",
                    )
                )
            )

            evidence_parts.append(
                str(
                    concept.get(
                        "description",
                        "",
                    )
                )
            )

        for hyperedge in hyperedges:

            evidence_parts.append(
                str(
                    hyperedge.get(
                        "label",
                        "",
                    )
                )
            )

            evidence_parts.append(
                str(
                    hyperedge.get(
                        "description",
                        "",
                    )
                )
            )

            members = hyperedge.get(
                "concepts",
                [],
            )

            if isinstance(
                members,
                list,
            ):

                evidence_parts.extend(
                    str(member)
                    for member in members
                )

        evidence_text = " ".join(
            evidence_parts
        ).lower()

        if query_keywords:

            matched_keywords = [
                keyword
                for keyword in query_keywords
                if keyword.lower()
                in evidence_text
            ]

            keyword_ratio = (
                len(matched_keywords)
                / len(query_keywords)
            )

            keyword_ratio = max(
                0.0,
                min(
                    1.0,
                    keyword_ratio,
                ),
            )

            scores.append(
                keyword_ratio
            )

            reasoning.append(
                "Query keyword support: "
                f"{len(matched_keywords)}/"
                f"{len(query_keywords)} "
                f"({keyword_ratio:.2f})"
            )

        # =====================================================
        # HYPERGRAPH CONCEPT SUPPORT
        # =====================================================

        if concepts:

            concept_support = min(
                1.0,
                0.40
                + (
                    min(
                        len(concepts),
                        5,
                    )
                    / 5.0
                )
                * 0.40,
            )

            scores.append(
                concept_support
            )

            reasoning.append(
                "Hypergraph concept support: "
                f"{len(concepts)} concept(s)"
            )

        # =====================================================
        # HYPEREDGE SUPPORT
        # =====================================================

        if hyperedges:

            max_edge_cardinality = max(
                int(
                    hyperedge.get(
                        "cardinality",
                        1,
                    )
                )
                for hyperedge in hyperedges
            )

            hyperedge_score = min(
                0.85,
                0.45
                + (
                    max_edge_cardinality
                    * 0.10
                ),
            )

            scores.append(
                hyperedge_score
            )

            reasoning.append(
                "Hypergraph edge support: "
                f"{len(hyperedges)} edge(s), "
                f"max cardinality="
                f"{max_edge_cardinality}"
            )

        # =====================================================
        # FINAL SCORE
        # =====================================================

        if not scores:

            return (
                0.0,
                [
                    "Evidence was retrieved, "
                    "but no usable relevance score "
                    "could be calculated."
                ],
            )

        relevance_score = (
            sum(scores)
            / len(scores)
        )

        relevance_score = max(
            0.0,
            min(
                1.0,
                relevance_score,
            ),
        )

        reasoning.append(
            "Final evidence relevance score: "
            f"{relevance_score:.2f}"
        )

        return (
            relevance_score,
            reasoning,
        )

    # =========================================================
    # KEYWORD PRESENCE
    # =========================================================

    def _keywords_present(
        self,
        keywords: List[str],
        chunks: List[Dict[str, Any]],
        concepts: List[Dict[str, Any]],
        hyperedges: List[Dict[str, Any]],
    ) -> bool:
        """Check whether enough query keywords occur in evidence."""

        if not keywords:
            return False

        evidence_parts: List[str] = []

        for chunk in chunks:

            evidence_parts.append(
                str(
                    chunk.get(
                        "content",
                        "",
                    )
                )
            )

        for concept in concepts:

            evidence_parts.append(
                str(
                    concept.get(
                        "name",
                        "",
                    )
                )
            )

            evidence_parts.append(
                str(
                    concept.get(
                        "description",
                        "",
                    )
                )
            )

        for hyperedge in hyperedges:

            evidence_parts.append(
                str(
                    hyperedge.get(
                        "label",
                        "",
                    )
                )
            )

            evidence_parts.append(
                str(
                    hyperedge.get(
                        "description",
                        "",
                    )
                )
            )

            members = hyperedge.get(
                "concepts",
                [],
            )

            if isinstance(
                members,
                list,
            ):

                evidence_parts.extend(
                    str(member)
                    for member in members
                )

        evidence_text = " ".join(
            evidence_parts
        ).lower()

        matched = sum(
            1
            for keyword in keywords
            if keyword.lower()
            in evidence_text
        )

        ratio = (
            matched
            / len(keywords)
        )

        return ratio >= 0.50

    # =========================================================
    # UTILITY
    # =========================================================

    @staticmethod
    def _unique_preserve_order(
        values: List[str],
    ) -> List[str]:
        """Remove duplicates while preserving order."""

        result: List[str] = []
        seen = set()

        for value in values:

            normalized = str(
                value
            ).strip()

            if not normalized:
                continue

            key = normalized.lower()

            if key in seen:
                continue

            seen.add(key)
            result.append(
                normalized
            )

        return result