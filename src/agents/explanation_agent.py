"""
Explanation Agent for EduHyperRAG.
Synthesizes verified evidence, hypergraph connections, source citations, and claim maps
into a concise, user-facing explainability package without exposing raw chain-of-thought.
"""

from typing import Any, Dict, List, Optional
from src.agents.state import VerificationAgentState
from src.evaluation.hallucination_checker import AnswerVerificationReport
from src.generation.explanation import (
    ClaimEvidenceDisplay,
    ExplainabilityReport,
    SourceChunkDisplay,
    SupportingConceptDisplay,
    SupportingHyperedgeDisplay,
)
from src.utils.logger import get_logger

logger = get_logger("explanation_agent")


class EduExplainabilityEngine:
    """Generates structured, evidence-based explainability reports."""

    def generate_explanation(
        self,
        verified_state: VerificationAgentState,
        answer_result: Dict[str, Any],
        verification_report: AnswerVerificationReport,
    ) -> ExplainabilityReport:
        """
        Builds a complete ExplainabilityReport.

        Args:
            verified_state: Verified state dictionary from Phase 5.
            answer_result: Generated answer output dictionary from Phase 6.
            verification_report: Verification report from Phase 7.

        Returns:
            ExplainabilityReport object.
        """
        query = verified_state["user_query"]
        answer_text = answer_result.get("answer", "")
        confidence = float(answer_result.get("confidence", 0.0))

        # Determine confidence level
        if not verified_state.get("is_sufficient", False) or confidence == 0.0:
            confidence_level = "Refused"
        elif confidence >= 0.75:
            confidence_level = "High"
        elif confidence >= 0.50:
            confidence_level = "Medium"
        else:
            confidence_level = "Low"

        # 1. Map Supporting Concepts
        supporting_concepts: List[SupportingConceptDisplay] = []
        seen_concepts = set()
        for con in verified_state.get("retrieved_concepts", []):
            name = con.get("name", "").strip()
            if name and name.lower() not in seen_concepts:
                seen_concepts.add(name.lower())
                supporting_concepts.append(
                    SupportingConceptDisplay(
                        name=name,
                        entity_type=con.get("entity_type", "Concept"),
                        description=con.get("description", ""),
                    )
                )

        # 2. Map Supporting Hyperedges
        supporting_hyperedges: List[SupportingHyperedgeDisplay] = []
        for hyp in verified_state.get("retrieved_hyperedges", []):
            supporting_hyperedges.append(
                SupportingHyperedgeDisplay(
                    hyperedge_id=hyp.get("hyperedge_id", ""),
                    label=hyp.get("label", hyp.get("hyperedge_id", "")),
                    cardinality=hyp.get("cardinality", len(hyp.get("concepts", []))),
                    concepts=hyp.get("concepts", []),
                    description=hyp.get("description", ""),
                )
            )

        # 3. Map Source Chunks
        source_chunks: List[SourceChunkDisplay] = []
        for ch in verified_state.get("retrieved_chunks", []):
            content_snippet = ch.get("content", "").replace("\n", " ").strip()
            if len(content_snippet) > 160:
                content_snippet = content_snippet[:157] + "..."
            
            meta = ch.get("metadata", {})
            source_file = meta.get("source_file", "unknown_source")

            source_chunks.append(
                SourceChunkDisplay(
                    chunk_id=ch.get("chunk_id", ""),
                    source_file=Path(source_file).name if source_file else "unknown_source",
                    snippet=content_snippet,
                )
            )

        # 4. Map Claim Evidences
        claim_evidences: List[ClaimEvidenceDisplay] = []
        for claim_res in verification_report.claims:
            claim_evidences.append(
                ClaimEvidenceDisplay(
                    claim=claim_res.claim,
                    status=claim_res.status,
                    score=claim_res.score,
                    supporting_excerpts=claim_res.evidence,
                )
            )

        # 5. Build Verification Badges
        badges: List[str] = []
        if verified_state.get("is_sufficient", False):
            badges.append("[OK] Evidence verified")
        else:
            badges.append("[!] Knowledge base evidence insufficient")

        if verification_report.unsupported_claims_count == 0:
            badges.append("[OK] No unsupported claims detected")
        else:
            badges.append(f"[!] {verification_report.unsupported_claims_count} unsupported claim(s) detected")

        if verified_state.get("sources"):
            badges.append(f"[OK] All sources traceable ({len(verified_state['sources'])} chunk reference(s))")

        report = ExplainabilityReport(
            query=query,
            answer=answer_text,
            confidence_level=confidence_level,
            confidence_score=confidence,
            supporting_concepts=supporting_concepts,
            supporting_hyperedges=supporting_hyperedges,
            source_chunks=source_chunks,
            claim_evidences=claim_evidences,
            verification_badges=badges,
        )

        logger.info(f"Generated ExplainabilityReport for query: '{query}' (Confidence: {confidence_level})")
        return report


from pathlib import Path
