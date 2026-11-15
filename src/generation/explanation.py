"""
Explainability and Evidence Display Data Models and Formatters.
Formats verified retrieval evidence, hyperedges, concepts, source chunks, and claim verifications
into concise, user-facing explainability reports.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SupportingConceptDisplay(BaseModel):
    name: str
    entity_type: str
    description: str


class SupportingHyperedgeDisplay(BaseModel):
    hyperedge_id: str
    label: str
    cardinality: int
    concepts: List[str]
    description: str


class SourceChunkDisplay(BaseModel):
    chunk_id: str
    source_file: str
    snippet: str


class ClaimEvidenceDisplay(BaseModel):
    claim: str
    status: str  # 'supported', 'partially_supported', 'unsupported'
    score: float
    supporting_excerpts: List[str]


class ExplainabilityReport(BaseModel):
    """Complete user-facing explainability report."""
    query: str
    answer: str
    confidence_level: str  # 'High', 'Medium', 'Low', 'Refused'
    confidence_score: float
    supporting_concepts: List[SupportingConceptDisplay] = Field(default_factory=list)
    supporting_hyperedges: List[SupportingHyperedgeDisplay] = Field(default_factory=list)
    source_chunks: List[SourceChunkDisplay] = Field(default_factory=list)
    claim_evidences: List[ClaimEvidenceDisplay] = Field(default_factory=list)
    verification_badges: List[str] = Field(default_factory=list)  # e.g. ["✓ Evidence verified", "✓ No unsupported claims"]

    def to_markdown(self) -> str:
        """Formats the explainability report as clean GitHub-style Markdown."""
        lines = []
        lines.append(f"### Question:\n{self.query}\n")
        lines.append(f"### Answer:\n{self.answer}\n")
        lines.append(f"**Confidence:** {self.confidence_level} ({self.confidence_score:.2f})\n")

        lines.append("### Supporting Concepts:")
        if self.supporting_concepts:
            for c in self.supporting_concepts:
                lines.append(f"- **{c.name}** ({c.entity_type}): {c.description}")
        else:
            lines.append("- None")

        lines.append("\n### Supporting Hyperedges:")
        if self.supporting_hyperedges:
            for h in self.supporting_hyperedges:
                members_str = ", ".join(h.concepts)
                lines.append(f"- **{h.label}** {{{members_str}}} [Size={h.cardinality}]: {h.description}")
        else:
            lines.append("- None")

        lines.append("\n### Source Evidence Chunks:")
        if self.source_chunks:
            for sc in self.source_chunks:
                lines.append(f"- **Source:** `{sc.source_file}` | **Chunk:** `{sc.chunk_id}`")
                lines.append(f"  > *\"{sc.snippet}\"*")
        else:
            lines.append("- None")

        lines.append("\n### Verification Badges:")
        for badge in self.verification_badges:
            lines.append(f"- {badge}")

        lines.append("\n### Claim-by-Claim Verification Map:")
        if self.claim_evidences:
            for ce in self.claim_evidences:
                status_icon = "[OK]" if ce.status == "supported" else "[!]" if ce.status == "partially_supported" else "[X]"
                lines.append(f"{status_icon} **Claim:** \"{ce.claim}\" [{ce.status.upper()}]")
                for ex in ce.supporting_excerpts:
                    lines.append(f"    - Evidence: {ex}")
        else:
            lines.append("- No claim verification map available.")

        return "\n".join(lines)
