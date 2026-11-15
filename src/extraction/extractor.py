"""
Concept and Hyperedge Extractor implementation.
Supports LLM API calls with robust JSON parsing, schema validation,
and a deterministic rule-based fallback engine for offline testing.
"""

import json
import re
from typing import Any, Dict, List, Optional
from src.config import config
from src.extraction.prompts import EXTRACTION_SYSTEM_PROMPT, build_extraction_user_prompt
from src.extraction.schema import (
    ChunkExtractionResult,
    EntityType,
    ExtractedEntity,
    HighOrderHyperedge,
    LowOrderRelation,
)
from src.preprocessing.chunker import Chunk
from src.utils.logger import get_logger

logger = get_logger("extractor")


class ConceptHyperedgeExtractor:
    """Extracts entities, pairwise relations, and hyperedges from text chunks."""

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or config.llm_api_key
        self.model_name = model_name or config.llm_model_name
        self.use_llm = bool(self.api_key and self.api_key.strip() and self.api_key != "your_api_key_here")

        if self.use_llm:
            logger.info(f"Initialized ConceptHyperedgeExtractor using LLM model: {self.model_name}")
        else:
            logger.info("No active LLM API key detected. ConceptHyperedgeExtractor running in deterministic Fallback Mode.")

    def extract_from_chunk(self, chunk: Chunk) -> ChunkExtractionResult:
        """
        Extracts knowledge components from a single chunk.

        Args:
            chunk: Chunk instance containing text content and metadata.

        Returns:
            ChunkExtractionResult containing validated entities, low-order relations, and hyperedges.
        """
        if self.use_llm:
            try:
                return self._extract_via_llm(chunk)
            except Exception as e:
                logger.warning(f"LLM extraction failed for chunk '{chunk.chunk_id}': {str(e)}. Falling back to rule-based extraction.")
                return self._extract_fallback(chunk)
        else:
            return self._extract_fallback(chunk)

    def _extract_via_llm(self, chunk: Chunk) -> ChunkExtractionResult:
        """Invokes LLM API to extract entities and hyperedges."""
        user_prompt = build_extraction_user_prompt(chunk.content, chunk.chunk_id)

        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=EXTRACTION_SYSTEM_PROMPT,
        )
        response = model.generate_content(user_prompt)
        raw_response = response.text if hasattr(response, "text") else str(response)

        parsed_json = self._clean_and_parse_json(raw_response)
        return self._build_result_from_json(parsed_json, chunk)

    def _clean_and_parse_json(self, response_text: str) -> Dict[str, Any]:
        """Strips markdown code blocks and parses JSON string."""
        text = response_text.strip()
        # Remove markdown code fences if present
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.MULTILINE)
        text = re.sub(r"\s*```$", "", text, flags=re.MULTILINE)
        text = text.strip()
        return json.loads(text)

    def _build_result_from_json(self, data: Dict[str, Any], chunk: Chunk) -> ChunkExtractionResult:
        """Validates JSON dict against Pydantic models and attaches source chunk IDs."""
        entities: List[ExtractedEntity] = []
        low_order: List[LowOrderRelation] = []
        high_order: List[HighOrderHyperedge] = []

        # Parse entities
        for raw_ent in data.get("entities", []):
            try:
                e_type = raw_ent.get("entity_type", "Concept")
                valid_type = EntityType.CONCEPT
                for et in EntityType:
                    if et.value.lower() == str(e_type).lower():
                        valid_type = et
                        break

                ent = ExtractedEntity(
                    entity_id=raw_ent.get("entity_id", f"ent_{len(entities):03d}"),
                    name=raw_ent.get("name", "").strip(),
                    entity_type=valid_type,
                    description=raw_ent.get("description", "").strip(),
                    source_chunk_ids=[chunk.chunk_id],
                )
                if ent.name:
                    entities.append(ent)
            except Exception as e:
                logger.debug(f"Skipping invalid entity in chunk {chunk.chunk_id}: {e}")

        # Parse low-order relations
        for raw_rel in data.get("low_order_relations", []):
            try:
                rel = LowOrderRelation(
                    relation_id=raw_rel.get("relation_id", f"rel_{len(low_order):03d}"),
                    source_entity=raw_rel.get("source_entity", "").strip(),
                    target_entity=raw_rel.get("target_entity", "").strip(),
                    relation_type=raw_rel.get("relation_type", "relates_to").strip(),
                    description=raw_rel.get("description", "").strip(),
                    source_chunk_ids=[chunk.chunk_id],
                )
                if rel.source_entity and rel.target_entity:
                    low_order.append(rel)
            except Exception as e:
                logger.debug(f"Skipping invalid low-order relation in chunk {chunk.chunk_id}: {e}")

        # Parse high-order hyperedges
        for raw_hyp in data.get("high_order_hyperedges", []):
            try:
                members = raw_hyp.get("member_entities", [])
                if isinstance(members, list) and len(members) >= 3:
                    hyp = HighOrderHyperedge(
                        hyperedge_id=raw_hyp.get("hyperedge_id", f"hyp_{len(high_order):03d}"),
                        member_entities=members,
                        relation_type=raw_hyp.get("relation_type", "hyper_relation").strip(),
                        description=raw_hyp.get("description", "").strip(),
                        cardinality=len(members),
                        source_chunk_ids=[chunk.chunk_id],
                    )
                    high_order.append(hyp)
            except Exception as e:
                logger.debug(f"Skipping invalid hyperedge in chunk {chunk.chunk_id}: {e}")

        return ChunkExtractionResult(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            entities=entities,
            low_order_relations=low_order,
            high_order_hyperedges=high_order,
        )

    def _extract_fallback(self, chunk: Chunk) -> ChunkExtractionResult:
        """
        Generic deterministic fallback extractor.

        This fallback is intentionally domain-independent. It does not contain
        predefined concepts, subjects, entities, or relationships. It extracts
        candidate concepts from the uploaded text and creates generic
        relationships/hyperedges based only on concepts appearing together
        in the same chunk.
        """

        text = chunk.content or ""

        entities: List[ExtractedEntity] = []
        low_order: List[LowOrderRelation] = []
        high_order: List[HighOrderHyperedge] = []

        # ---------------------------------------------------------
        # 1. Extract candidate concepts from the chunk
        # ---------------------------------------------------------

        candidates = []

        # Multi-word capitalized terms
        candidates.extend(
            re.findall(
                r"\b[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){1,4}\b",
                text,
            )
        )

        # Important technical terms / noun phrases
        candidates.extend(
            re.findall(
                r"\b[A-Za-z][A-Za-z0-9-]{2,}(?:\s+[A-Za-z][A-Za-z0-9-]{2,}){0,3}\b",
                text,
            )
        )

        # ---------------------------------------------------------
        # 2. Remove common stopwords/noise
        # ---------------------------------------------------------

        stopwords = {
            "the", "and", "or", "but", "for", "with", "from",
            "this", "that", "these", "those", "are", "was",
            "were", "been", "being", "have", "has", "had",
            "into", "onto", "about", "above", "below", "between",
            "through", "during", "before", "after", "which",
            "where", "when", "while", "what", "how", "why",
            "who", "whose", "their", "there", "here", "then",
            "than", "also", "such", "using", "used", "use",
            "can", "could", "may", "might", "will", "would",
            "should", "shall", "must", "more", "most", "some",
            "any", "each", "other", "another", "very", "often",
            "typically", "generally", "important", "example",
            "examples", "following", "following are",
        }

        cleaned_candidates = []

        for candidate in candidates:
            candidate = re.sub(r"\s+", " ", candidate).strip()

            if not candidate:
                continue

            words = candidate.lower().split()

            # Ignore phrases made entirely of stopwords
            if all(word in stopwords for word in words):
                continue

            # Ignore very short/common candidates
            if len(candidate) < 3:
                continue

            cleaned_candidates.append(candidate)

        # ---------------------------------------------------------
        # 3. Deduplicate concepts while preserving order
        # ---------------------------------------------------------

        seen = set()
        concepts = []

        for candidate in cleaned_candidates:
            key = candidate.lower()

            if key in seen:
                continue

            seen.add(key)
            concepts.append(candidate)

        # Keep the graph manageable
        concepts = concepts[:30]

        # ---------------------------------------------------------
        # 4. Create generic entity nodes
        # ---------------------------------------------------------

        for idx, concept in enumerate(concepts):
            entity_id = f"{chunk.chunk_id}_ent_{idx:03d}"

            entities.append(
                ExtractedEntity(
                    entity_id=entity_id,
                    name=concept,
                    entity_type=EntityType.CONCEPT,
                    description=f"Concept identified from the uploaded document: {concept}.",
                    source_chunk_ids=[chunk.chunk_id],
                )
            )

        # ---------------------------------------------------------
        # 5. Create generic pairwise relationships
        # ---------------------------------------------------------

        for idx in range(len(concepts) - 1):
            source = concepts[idx]
            target = concepts[idx + 1]

            low_order.append(
                LowOrderRelation(
                    relation_id=f"{chunk.chunk_id}_rel_{idx:03d}",
                    source_entity=source,
                    target_entity=target,
                    relation_type="co_occurs_with",
                    description=(
                        f"{source} and {target} occur together in the same "
                        f"source passage."
                    ),
                    source_chunk_ids=[chunk.chunk_id],
                )
            )

        # ---------------------------------------------------------
        # 6. Create generic hyperedges
        #
        # A hyperedge connects multiple concepts appearing in the
        # same chunk. No domain-specific assumptions are made.
        # ---------------------------------------------------------

        if len(concepts) >= 3:
            group_size = min(6, len(concepts))

            for start in range(0, len(concepts), group_size):
                members = concepts[start:start + group_size]

                if len(members) < 3:
                    continue

                high_order.append(
                    HighOrderHyperedge(
                        hyperedge_id=(
                            f"{chunk.chunk_id}_hyp_"
                            f"{len(high_order):03d}"
                        ),
                        member_entities=members,
                        relation_type="co_occurrence_group",
                        description=(
                            "Multiple concepts occurring together in "
                            "the same source chunk."
                        ),
                        cardinality=len(members),
                        source_chunk_ids=[chunk.chunk_id],
                    )
                )

        # ---------------------------------------------------------
        # 7. Return extraction result
        # ---------------------------------------------------------

        return ChunkExtractionResult(
            chunk_id=chunk.chunk_id,
            doc_id=chunk.doc_id,
            entities=entities,
            low_order_relations=low_order,
            high_order_hyperedges=high_order,
        )
