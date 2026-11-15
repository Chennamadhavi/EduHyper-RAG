"""
Extraction Pipeline for EduHyperRAG.
Processes document chunks, extracts entities and hyperedges,
deduplicates components while preserving source chunk IDs, and persists JSON outputs.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from src.config import config
from src.extraction.extractor import ConceptHyperedgeExtractor
from src.extraction.schema import (
    ChunkExtractionResult,
    ExtractedEntity,
    HighOrderHyperedge,
    KnowledgeBaseExtractions,
    LowOrderRelation,
)
from src.preprocessing.chunker import Chunk
from src.utils.file_io import read_json, save_json
from src.utils.logger import get_logger

logger = get_logger("extraction_pipeline")


class ExtractionPipeline:
    """Orchestrates Phase 2 concept, relation, and hyperedge extractions."""

    def __init__(self, extractor: Optional[ConceptHyperedgeExtractor] = None):
        self.extractor = extractor or ConceptHyperedgeExtractor()

    def process_chunks_file(self, chunks_json_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Processes a chunk JSON file (e.g. photosynthesis_chapter_semantic_chunks.json).

        Args:
            chunks_json_path: Path to the chunks JSON file.

        Returns:
            Dict containing extraction summary statistics and saved JSON path.
        """
        path = Path(chunks_json_path)
        if not path.exists():
            raise FileNotFoundError(f"Chunks file not found: {path}")

        raw_chunks = read_json(path)
        chunks = [Chunk(**c) for c in raw_chunks]
        if not chunks:
            raise ValueError(f"No valid chunks found in {path}")

        doc_id = chunks[0].doc_id
        logger.info(f"Starting Phase 2 Extraction for doc '{doc_id}' across {len(chunks)} chunk(s)...")

        chunk_results: List[ChunkExtractionResult] = []
        for chunk in chunks:
            res = self.extractor.extract_from_chunk(chunk)
            chunk_results.append(res)

        # Merge and deduplicate extractions across chunks
        merged_kb = self._merge_extractions(doc_id, chunk_results)

        # Save output JSON
        output_filename = f"extractions_{doc_id}.json"
        output_path = config.processed_data_dir / output_filename
        save_json(merged_kb.model_dump(), output_path)

        avg_hyperedge_cardinality = (
            sum(h.cardinality for h in merged_kb.high_order_hyperedges) / len(merged_kb.high_order_hyperedges)
            if merged_kb.high_order_hyperedges
            else 0.0
        )

        summary = {
            "doc_id": doc_id,
            "chunks_processed": len(chunks),
            "total_entities": len(merged_kb.entities),
            "total_low_order_relations": len(merged_kb.low_order_relations),
            "total_high_order_hyperedges": len(merged_kb.high_order_hyperedges),
            "avg_hyperedge_cardinality": round(avg_hyperedge_cardinality, 2),
            "extraction_output_path": str(output_path),
        }

        logger.info(
            f"Extraction completed for '{doc_id}': {summary['total_entities']} entities, "
            f"{summary['total_low_order_relations']} low-order relations, "
            f"{summary['total_high_order_hyperedges']} high-order hyperedges."
        )
        return summary

    def _merge_extractions(
        self, doc_id: str, chunk_results: List[ChunkExtractionResult]
    ) -> KnowledgeBaseExtractions:
        """Deduplicates entities, relations, and hyperedges across chunks while keeping all source chunk IDs."""
        entity_map: Dict[str, ExtractedEntity] = {}
        low_order_map: Dict[str, LowOrderRelation] = {}
        high_order_map: Dict[str, HighOrderHyperedge] = {}

        for res in chunk_results:
            # Merge Entities
            for ent in res.entities:
                key = ent.name.strip().lower()
                if key in entity_map:
                    # Append source chunk ID if not present
                    for cid in ent.source_chunk_ids:
                        if cid not in entity_map[key].source_chunk_ids:
                            entity_map[key].source_chunk_ids.append(cid)
                    # Use longer/richer description if available
                    if len(ent.description) > len(entity_map[key].description):
                        entity_map[key].description = ent.description
                else:
                    entity_map[key] = ent.model_copy(deep=True)

            # Merge Low-Order Relations
            for rel in res.low_order_relations:
                key = f"{rel.source_entity.strip().lower()}--{rel.relation_type.strip().lower()}-->{rel.target_entity.strip().lower()}"
                if key in low_order_map:
                    for cid in rel.source_chunk_ids:
                        if cid not in low_order_map[key].source_chunk_ids:
                            low_order_map[key].source_chunk_ids.append(cid)
                else:
                    low_order_map[key] = rel.model_copy(deep=True)

            # Merge High-Order Hyperedges
            for hyp in res.high_order_hyperedges:
                sorted_members = sorted([m.strip().lower() for m in hyp.member_entities])
                key = f"{hyp.relation_type.strip().lower()}::" + "|".join(sorted_members)
                if key in high_order_map:
                    for cid in hyp.source_chunk_ids:
                        if cid not in high_order_map[key].source_chunk_ids:
                            high_order_map[key].source_chunk_ids.append(cid)
                else:
                    high_order_map[key] = hyp.model_copy(deep=True)

        return KnowledgeBaseExtractions(
            doc_id=doc_id,
            entities=list(entity_map.values()),
            low_order_relations=list(low_order_map.values()),
            high_order_hyperedges=list(high_order_map.values()),
            metadata={"extraction_strategy": "merged_chunks"},
        )
