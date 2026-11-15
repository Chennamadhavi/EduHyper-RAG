"""
Hallucination Checker and Claim Verification Engine for EduHyperRAG.
Extracts discrete factual claims from generated answers, verifies each claim line-by-line
against retrieved evidence, computes support scores, and triggers correction/regeneration.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from src.config import config
from src.utils.logger import get_logger

logger = get_logger("hallucination_checker")


class ClaimVerificationResult(BaseModel):
    """Result schema for individual claim verification."""
    claim: str = Field(..., description="Atomic factual claim extracted from answer")
    status: str = Field(..., description="Classification: 'supported', 'partially_supported', or 'unsupported'")
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence excerpts from source chunks/hyperedges")
    score: float = Field(..., description="Support confidence score for this claim (0.0 to 1.0)")


class AnswerVerificationReport(BaseModel):
    """Overall verification report for a generated answer."""
    answer: str
    claims: List[ClaimVerificationResult]
    support_score: float = Field(..., description="Overall support score (ratio of supported claims)")
    unsupported_claims_count: int
    decision: str = Field(..., description="'ACCEPT', 'REGENERATE', or 'REJECT_INSUFFICIENT'")
    feedback: str = Field(..., description="Detailed verification explanation")


class HallucinationChecker:
    """Verifies generated answers claim-by-claim against retrieved evidence."""

    def __init__(self, min_support_score: float = 0.70, max_unsupported_ratio: float = 0.25):
        """
        Args:
            min_support_score: Minimum required overall support score (0.0 to 1.0) to ACCEPT answer.
            max_unsupported_ratio: Maximum allowed ratio of unsupported claims before REGENERATE.
        """
        self.min_support_score = min_support_score
        self.max_unsupported_ratio = max_unsupported_ratio

    def verify_answer(
        self,
        answer_text: str,
        retrieved_chunks: List[Dict[str, Any]],
        retrieved_hyperedges: List[Dict[str, Any]],
        retrieved_concepts: Optional[List[Dict[str, Any]]] = None,
    ) -> AnswerVerificationReport:
        """
        Extracts claims and verifies each claim against retrieved evidence.

        Args:
            answer_text: Generated answer text.
            retrieved_chunks: List of retrieved evidence chunks.
            retrieved_hyperedges: List of retrieved hyperedges.
            retrieved_concepts: Optional list of retrieved concepts.

        Returns:
            AnswerVerificationReport object containing claim details, overall score, and decision.
        """
        if not answer_text or not answer_text.strip():
            return AnswerVerificationReport(
                answer="",
                claims=[],
                support_score=0.0,
                unsupported_claims_count=0,
                decision="REJECT_INSUFFICIENT",
                feedback="Empty answer provided.",
            )

        # Check if answer is an explicit refusal
        if "insufficient evidence" in answer_text.lower():
            return AnswerVerificationReport(
                answer=answer_text,
                claims=[],
                support_score=1.0,
                unsupported_claims_count=0,
                decision="ACCEPT",
                feedback="Answer is an explicit, grounded refusal due to insufficient evidence.",
            )

        # 1. Extract atomic claims from answer text
        claims = self._extract_claims(answer_text)
        if not claims:
            return AnswerVerificationReport(
                answer=answer_text,
                claims=[],
                support_score=1.0,
                unsupported_claims_count=0,
                decision="ACCEPT",
                feedback="No factual claims extracted.",
            )

        # Build evidence corpus string and reference dictionary
        evidence_corpus, evidence_map = self._build_evidence_corpus(
            retrieved_chunks, retrieved_hyperedges, retrieved_concepts or []
        )

        verified_claims: List[ClaimVerificationResult] = []
        supported_count = 0
        partially_supported_count = 0

        # 2. Verify each claim line-by-line against evidence
        for claim in claims:
            res = self._verify_single_claim(claim, evidence_corpus, evidence_map)
            verified_claims.append(res)
            if res.status == "supported":
                supported_count += 1
            elif res.status == "partially_supported":
                partially_supported_count += 1

        total_claims = len(claims)
        # Calculate empirical support score: supported counts 1.0, partially supported counts 0.5
        effective_supported = supported_count + (0.5 * partially_supported_count)
        support_score = round(effective_supported / total_claims, 4)
        unsupported_count = total_claims - supported_count - partially_supported_count
        unsupported_ratio = unsupported_count / total_claims

        # 3. Determine decision based on threshold rules
        if support_score >= self.min_support_score and unsupported_ratio <= self.max_unsupported_ratio:
            decision = "ACCEPT"
            feedback = f"Answer Accepted: {supported_count}/{total_claims} claims fully supported (Support score: {support_score:.2f})."
        elif unsupported_count > 0:
            decision = "REGENERATE"
            feedback = (
                f"Answer Regeneration Required: {unsupported_count}/{total_claims} claims unsupported "
                f"(Unsupported ratio: {unsupported_ratio:.2f} > threshold {self.max_unsupported_ratio})."
            )
        else:
            decision = "REJECT_INSUFFICIENT"
            feedback = "Answer rejected due to insufficient grounding evidence."

        logger.info(f"Answer Verification: decision={decision}, support_score={support_score:.2f}, unsupported={unsupported_count}")

        return AnswerVerificationReport(
            answer=answer_text,
            claims=verified_claims,
            support_score=support_score,
            unsupported_claims_count=unsupported_count,
            decision=decision,
            feedback=feedback,
        )

    def _extract_claims(self, text: str) -> List[str]:
        """Splits answer text into atomic factual claim sentences, stripping formatting headers."""
        raw_lines = text.split("\n")
        claims = []
        for line in raw_lines:
            line = line.strip()
            # Ignore headers, bullet points markers, or blank lines
            if not line or line.startswith("#") or line.startswith("**") and line.endswith("**"):
                continue
            line = re.sub(r"^\s*[-*]\s+", "", line)
            
            # Split line into sentences
            sentences = re.split(r"(?<=[.!?])\s+", line)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 15 and not s_clean.startswith("Educational Summary"):
                    claims.append(s_clean)
        return claims

    def _build_evidence_corpus(
        self,
        chunks: List[Dict[str, Any]],
        hyperedges: List[Dict[str, Any]],
        concepts: List[Dict[str, Any]],
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """Builds evidence string and list of (source_tag, text) pairs for matching."""
        evidence_pairs: List[Tuple[str, str]] = []

        for c in chunks:
            tag = f"Chunk {c['chunk_id']}"
            evidence_pairs.append((tag, c["content"]))

        for h in hyperedges:
            tag = f"Hyperedge {h['hyperedge_id']} ({h.get('label', '')})"
            content = f"{' '.join(h['concepts'])} {h.get('description', '')}"
            evidence_pairs.append((tag, content))

        for con in concepts:
            tag = f"Concept {con['name']}"
            content = f"{con['name']} {con.get('description', '')}"
            evidence_pairs.append((tag, content))

        full_corpus = " ".join([text for _, text in evidence_pairs]).lower()
        return full_corpus, evidence_pairs

    def _verify_single_claim(
        self, claim: str, full_evidence_corpus: str, evidence_pairs: List[Tuple[str, str]]
    ) -> ClaimVerificationResult:
        """Compares a single claim against evidence pairs."""
        # Clean claim text (strip chunk citations like [photosynthesis_chapter_semantic_0001])
        clean_claim = re.sub(r"\[[^\]]+\]", "", claim).strip()
        claim_words = [w.lower() for w in re.findall(r"\b\w+\b", clean_claim) if len(w) > 3]

        if not claim_words:
            return ClaimVerificationResult(
                claim=claim, status="supported", evidence=["Structural header/formatting line."], score=1.0
            )

        matched_evidence: List[str] = []
        matched_words_count = 0

        # Search matching evidence excerpts
        for tag, content in evidence_pairs:
            content_lower = content.lower()
            matches = [w for w in claim_words if w in content_lower]
            match_ratio = len(matches) / len(claim_words)

            if match_ratio >= 0.40:
                matched_evidence.append(f"{tag}: \"{content[:150]}...\"")
                matched_words_count = max(matched_words_count, len(matches))

        overall_ratio = matched_words_count / len(claim_words) if claim_words else 1.0

        if overall_ratio >= 0.65 or len(matched_evidence) >= 2:
            status = "supported"
            score = round(min(1.0, 0.70 + (overall_ratio * 0.30)), 2)
        elif overall_ratio >= 0.35 or len(matched_evidence) == 1:
            status = "partially_supported"
            score = round(min(0.69, 0.40 + (overall_ratio * 0.30)), 2)
        else:
            status = "unsupported"
            score = round(overall_ratio * 0.30, 2)
            matched_evidence = ["No matching evidence found in retrieved source chunks."]

        return ClaimVerificationResult(
            claim=claim,
            status=status,
            evidence=matched_evidence[:2],  # Keep top 2 supporting evidence items visible
            score=score,
        )
