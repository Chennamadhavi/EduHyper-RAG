"""
Unit tests for Phase 2 Concept, Relation, and Hyperedge Extraction.
"""

import tempfile
from pathlib import Path
import pytest
from pydantic import ValidationError

from src.extraction.extractor import ConceptHyperedgeExtractor
from src.extraction.pipeline import ExtractionPipeline
from src.extraction.schema import (
    EntityType,
    ExtractedEntity,
    HighOrderHyperedge,
    LowOrderRelation,
)
from src.preprocessing.chunker import Chunk, ChunkingStrategy
from src.utils.file_io import save_json, read_json


def test_extracted_entity_schema():
    ent = ExtractedEntity(
        entity_id="ent_001",
        name="Chloroplast",
        entity_type=EntityType.ORGANELLE,
        description="Double-membrane organelle.",
        source_chunk_ids=["chunk_001"],
    )
    assert ent.name == "Chloroplast"
    assert ent.entity_type == EntityType.ORGANELLE
    assert "chunk_001" in ent.source_chunk_ids


def test_hyperedge_cardinality_validation():
    # Valid hyperedge (>= 3 members)
    valid_hyp = HighOrderHyperedge(
        hyperedge_id="hyp_001",
        member_entities=["Photosystem II", "P680", "Water Photolysis"],
        relation_type="water_splitting",
        description="Water splitting complex in PSII.",
        cardinality=3,
        source_chunk_ids=["chunk_001"],
    )
    assert valid_hyp.cardinality == 3

    # Invalid hyperedge (< 3 members) should raise ValidationError
    with pytest.raises(ValidationError):
        HighOrderHyperedge(
            hyperedge_id="hyp_002",
            member_entities=["P680", "Water"],
            relation_type="invalid_binary",
            description="Only 2 members",
            cardinality=2,
            source_chunk_ids=["chunk_001"],
        )


def test_extractor_fallback():
    extractor = ConceptHyperedgeExtractor(api_key="")
    sample_chunk = Chunk(
        chunk_id="chunk_photosynthesis_001",
        doc_id="photosynthesis_chapter",
        chunk_index=0,
        content=(
            "Photosystem II reaction center P680 uses the Oxygen-Evolving Complex for water photolysis, "
            "releasing protons, electrons, and oxygen gas in the thylakoid lumen."
        ),
        word_count=24,
        token_count_approx=30,
        start_char=0,
        end_char=180,
        chunking_strategy=ChunkingStrategy.SEMANTIC,
        metadata={},
    )
    
    result = extractor.extract_from_chunk(sample_chunk)
    assert len(result.entities) >= 3
    assert len(result.high_order_hyperedges) >= 1
    assert all(h.cardinality >= 3 for h in result.high_order_hyperedges)
    assert result.entities[0].source_chunk_ids == ["chunk_photosynthesis_001"]


def test_extraction_pipeline_e2e():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        chunks_file = tmp_path / "test_chunks.json"
        
        sample_chunk_dict = [
            Chunk(
                chunk_id="chunk_test_001",
                doc_id="test_doc",
                chunk_index=0,
                content="Photosystem II reaction center P680 undergoes water photolysis in the chloroplast.",
                word_count=12,
                token_count_approx=15,
                start_char=0,
                end_char=100,
                chunking_strategy=ChunkingStrategy.SEMANTIC,
                metadata={},
            ).model_dump()
        ]
        save_json(sample_chunk_dict, chunks_file)
        
        from src.config import config
        orig_processed = config.processed_data_dir
        config.processed_data_dir = tmp_path
        
        try:
            pipeline = ExtractionPipeline()
            summary = pipeline.process_chunks_file(chunks_file)
            
            assert summary["doc_id"] == "test_doc"
            assert summary["total_entities"] > 0
            assert Path(summary["extraction_output_path"]).exists()
            
            saved_data = read_json(summary["extraction_output_path"])
            assert "entities" in saved_data
            assert "high_order_hyperedges" in saved_data
        finally:
            config.processed_data_dir = orig_processed
