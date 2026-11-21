"""
Educational Answer Generation Engine for EduHyperRAG.
Generates factually grounded answers using ONLY verified retrieved evidence from Phase 5.
Tracks supporting source chunks, hyperedge IDs, confidence, and potential unsupported claims.
"""

import json
import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.agents.state import VerificationAgentState
from src.config import config
from src.utils.logger import get_logger

logger = get_logger("answer_generator")

ANSWER_SYSTEM_PROMPT = """
You are an expert Educational AI Tutor.

Generate a clear and useful answer to the user's question using ONLY the
verified evidence supplied in the prompt.

The educational material may belong to ANY subject or domain.

The source may contain content from:
Computer Science, Artificial Intelligence, Machine Learning, Mathematics,
Physics, Chemistry, Biology, Electronics, Robotics, Engineering, Business,
Economics, History, Literature, or any other academic subject.

Do NOT assume the subject.

STRICT GROUNDING RULES:

1. Use ONLY the supplied verified document chunks, concepts, and hyperedges.

2. Do NOT use outside knowledge.

3. Do NOT introduce facts that are absent from the retrieved evidence.

4. Do NOT rely on examples from this instruction.

5. If the evidence is insufficient, explicitly state:

"Based on the provided educational materials, there is insufficient
evidence to answer this question."

6. Every factual claim must be supported by the retrieved evidence.

7. Preserve the terminology used in the source material.

8. Clearly reference supporting source chunk IDs using their actual IDs,
for example [document_chunk_0001].

9. Do not invent chunk IDs or hyperedge IDs.

10. If a hyperedge is used, reference its actual hyperedge ID.

11. Provide a comprehensive, well-structured educational answer based on the retrieved evidence. If the source material contains specific factors, key principles, classifications, definitions, or examples, include them systematically using bullet points and clear headings so students receive the full educational detail from the source text rather than an overly brief summary.

12. Do not add subject-specific information that is not present in the
retrieved evidence.

Return ONLY valid JSON.

Required format:

{
  "answer": "Grounded educational answer with actual source chunk references.",
  "supporting_chunks": ["actual_chunk_id"],
  "supporting_hyperedges": ["actual_hyperedge_id"],
  "confidence": 0.85,
  "unsupported_claims": []
}
"""

class AnswerOutput(BaseModel):
    """Schema for Phase 6 answer generation output."""
    answer: str = Field(..., description="Educational answer text grounded in verified evidence")
    supporting_chunks: List[str] = Field(default_factory=list, description="IDs of source chunks used")
    supporting_hyperedges: List[str] = Field(default_factory=list, description="IDs of supporting hyperedges used")
    confidence: float = Field(..., description="Generation confidence score (0.0 to 1.0)")
    unsupported_claims: List[str] = Field(default_factory=list, description="Any ungrounded claims detected")


class EducationalAnswerGenerator:
    """Answer generator enforcing evidence grounding and source citation."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.llm_api_key
        self.model_name = model_name or config.llm_model_name
        self.use_llm = bool(self.api_key and self.api_key.strip() and self.api_key != "your_api_key_here")

        if self.use_llm:
            logger.info(f"Initialized EducationalAnswerGenerator using LLM model: {self.model_name}")
        else:
            logger.info("EducationalAnswerGenerator running in Grounded Fallback Generation Mode.")

    def generate_answer(self, verified_state: VerificationAgentState) -> Dict[str, Any]:
        """
        Generates grounded answer from Phase 5 verified state.

        Args:
            verified_state: State dictionary output by Phase 5 LangGraph workflow.

        Returns:
            JSON-serializable dictionary matching AnswerOutput schema.
        """
        query = verified_state["user_query"]
        is_sufficient = verified_state.get("is_sufficient", False)
        chunks = verified_state.get("retrieved_chunks", [])
        hyperedges = verified_state.get("retrieved_hyperedges", [])
        concepts = verified_state.get("retrieved_concepts", [])
        sources = verified_state.get("sources", [])

        # If evidence is marked insufficient by agent, return explicit refusal answer
        if not is_sufficient or not chunks:
            reason = verified_state.get(
                "verification_reasoning",
                "The available knowledge base does not contain sufficient factual evidence to answer this question."
            )
            out = AnswerOutput(
                answer=(
                    f"Based on the provided educational materials, there is insufficient evidence to answer your question "
                    f"('{query}'). Reason: {reason}"
                ),
                supporting_chunks=[],
                supporting_hyperedges=[],
                confidence=0.0,
                unsupported_claims=[],
            )
            return out.model_dump()

        # Generate answer using LLM or Fallback
        if self.use_llm:
            try:
                return self._generate_via_llm(query, chunks, hyperedges, concepts, sources, verified_state)
            except Exception as e:
                logger.exception("GEMINI GENERATION FAILED")
                raise
        else:
            return self._generate_fallback(query, chunks, hyperedges, concepts, sources, verified_state)

    def _generate_via_llm(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        hyperedges: List[Dict[str, Any]],
        concepts: List[Dict[str, Any]],
        sources: List[str],
        state: VerificationAgentState,
    ) -> Dict[str, Any]:
        """Invokes Gemini using the current google-genai SDK."""

        context_prompt = self._build_context_prompt(
            query,
            chunks,
            hyperedges,
            concepts,
        )

        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        response = client.models.generate_content(
            model=self.model_name,
            contents=context_prompt,
            config=types.GenerateContentConfig(
                system_instruction=ANSWER_SYSTEM_PROMPT,
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )

        raw_text = (
            response.text
            if hasattr(response, "text")
            else str(response)
        )

        # Remove Markdown JSON code fences if Gemini returns them
        raw_text = re.sub(
            r"^```(?:json)?\s*",
            "",
            raw_text.strip(),
            flags=re.MULTILINE,
        )
        raw_text = re.sub(
            r"\s*```$",
            "",
            raw_text.strip(),
            flags=re.MULTILINE,
        )

        # Parse Gemini JSON response
        parsed = json.loads(raw_text.strip())

        out = AnswerOutput(
            answer=parsed.get("answer", ""),
            supporting_chunks=parsed.get(
                "supporting_chunks",
                sources,
            ),
            supporting_hyperedges=parsed.get(
                "supporting_hyperedges",
                [h["hyperedge_id"] for h in hyperedges],
            ),
            confidence=float(
                parsed.get(
                    "confidence",
                    state.get("confidence", 0.85),
                )
            ),
            unsupported_claims=parsed.get(
                "unsupported_claims",
                [],
            ),
        )

        return out.model_dump()

    def _generate_fallback(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        hyperedges: List[Dict[str, Any]],
        concepts: List[Dict[str, Any]],
        sources: List[str],
        state: VerificationAgentState,
    ) -> Dict[str, Any]:
        """
        Deterministic, fully-grounded educational answer synthesis for testing and offline execution.
        Combines top evidence chunks, concept definitions, and hyperedges with source chunk citations.
        """
        top_chunks = sorted(chunks, key=lambda c: c.get("relevance_score", 0.0), reverse=True)[:2]
        supporting_chunk_ids = [c["chunk_id"] for c in top_chunks]
        supporting_hyperedge_ids = [h["hyperedge_id"] for h in hyperedges[:2]]

        # Synthesize answer paragraphs
        answer_parts = []
        answer_parts.append(f"**Educational Summary for Query:** *\"{query}\"*\n")

        # 1. Fact Statements from Top Chunks
        answer_parts.append("**Retrieved Evidence Facts:**")
        for chunk in top_chunks:
            cid = chunk["chunk_id"]
            # Extract first two sentences of chunk content
            sentences = [s.strip() for s in chunk["content"].split(".") if s.strip() and not s.startswith("#")][:2]
            fact_text = ". ".join(sentences) + "."
            answer_parts.append(f"- {fact_text} [{cid}]")

        # 2. Relational Hyperedge Structures
        if hyperedges:
            answer_parts.append("\n**High-Order Relational Mechanisms:**")
            for edge in hyperedges[:2]:
                members = ", ".join(edge["concepts"])
                hid = edge["hyperedge_id"]
                label = edge.get("label", hid)
                desc = edge.get("description", "")
                srcs = ", ".join([f"[{s}]" for s in edge.get("source_chunk_ids", [])])
                answer_parts.append(f"- **{label}** ({members}): {desc} {srcs}")

                # 3. Explanatory Synthesis
        #
        # IMPORTANT:
        # This must remain completely domain-independent.
        # Never insert subject-specific facts here.
        if top_chunks:
            answer_parts.append(
                "\n**Explanatory Synthesis:**\n"
                "The answer above is synthesized exclusively from the "
                "verified evidence retrieved from the uploaded educational "
                "materials. The cited chunks provide the factual basis "
                "for the response."
            )

        full_answer = "\n".join(answer_parts)
        confidence = state.get("confidence", 0.85)

        out = AnswerOutput(
            answer=full_answer,
            supporting_chunks=supporting_chunk_ids,
            supporting_hyperedges=supporting_hyperedge_ids,
            confidence=confidence,
            unsupported_claims=[],
        )
        return out.model_dump()

    def _build_context_prompt(
        self,
        query: str,
        chunks: List[Dict[str, Any]],
        hyperedges: List[Dict[str, Any]],
        concepts: List[Dict[str, Any]],
    ) -> str:
        """Constructs prompt containing verified evidence for LLM generation."""
        lines = [f"USER QUERY: {query}\n", "VERIFIED RETRIEVED EVIDENCE:"]
        
        lines.append("\n--- DOCUMENT CHUNKS ---")
        for c in chunks:
            lines.append(f"[{c['chunk_id']}] {c['content']}\n")

        lines.append("\n--- HIGH-ORDER HYPEREDGES ---")
        for h in hyperedges:
            lines.append(
                f"[{h['hyperedge_id']}] ({h.get('label', '')}) Members: {h['concepts']}. "
                f"Description: {h.get('description', '')}. Sources: {h.get('source_chunk_ids', [])}"
            )

        lines.append("\n--- CONCEPT DEFINITIONS ---")
        for con in concepts[:5]:
            lines.append(f"[{con['name']}] ({con.get('entity_type', '')}): {con.get('description', '')}")

        lines.append("\nRespond ONLY in valid JSON matching the AnswerOutput schema.")
        return "\n".join(lines)

