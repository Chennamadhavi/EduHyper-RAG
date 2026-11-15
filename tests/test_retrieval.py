"""
Unit tests for Phase 4 Retrieval Engines (Semantic, Hypergraph, and Hybrid).
"""

import tempfile
from pathlib import Path
import pytest

from src.preprocessing.chunker import Chunk, ChunkingStrategy
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.hypergraph_retriever import HypergraphRetriever
from src.retrieval.semantic_retriever import SemanticRetriever
from src.utils.file_io import save_json


def test_semantic_retriever():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        retriever = SemanticRetriever(
            collection_name="test_collection",
            persist_directory=Path(tmp_dir) / "chroma"
        )
        sample_chunks = [
            Chunk(
                chunk_id="chunk_001",
                doc_id="doc1",
                chunk_index=0,
                content="Water photolysis in Photosystem II splits H2O into oxygen and protons.",
                word_count=11,
                token_count_approx=15,
                start_char=0,
                end_char=80,
                chunking_strategy=ChunkingStrategy.SEMANTIC,
                metadata={"source_file": "doc1.txt"},
            ),
            Chunk(
                chunk_id="chunk_002",
                doc_id="doc1",
                chunk_index=1,
                content="Chlorophyll pigments absorb solar energy in thylakoid membranes.",
                word_count=9,
                token_count_approx=12,
                start_char=81,
                end_char=150,
                chunking_strategy=ChunkingStrategy.SEMANTIC,
                metadata={"source_file": "doc1.txt"},
            ),
        ]
        
        indexed = retriever.index_chunks(sample_chunks)
        assert indexed == 2

        results = retriever.search("water photolysis oxygen", top_k=1)
        assert len(results) == 1
        assert results[0].chunk_id == "chunk_001"
        assert results[0].relevance_score > 0.0
        assert results[0].retrieval_method == "semantic"


def test_hypergraph_retriever():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_path = Path(tmp_dir)
        hypergraph_file = tmp_path / "hypergraph.json"
        
        # Save sample hypergraph JSON
        sample_data = {
            "metadata": {"num_nodes": 3, "num_hyperedges": 1},
            "concepts": {
                "Chlorophyll": {"concept_id": "Chlorophyll", "name": "Chlorophyll", "entity_type": "Pigment", "description": "Absorbs light", "source_chunk_ids": ["chunk_002"]},
                "Light": {"concept_id": "Light", "name": "Light", "entity_type": "Factor", "description": "Solar light", "source_chunk_ids": ["chunk_002"]},
                "P680": {"concept_id": "P680", "name": "P680", "entity_type": "Pigment", "description": "PSII reaction center", "source_chunk_ids": ["chunk_001"]},
            },
            "hyperedges": {
                "H1": {
                    "hyperedge_id": "H1",
                    "label": "light_harvesting",
                    "concepts": ["Chlorophyll", "Light", "P680"],
                    "description": "Light excitation of chlorophyll transfers energy to P680.",
                    "source_chunk_ids": ["chunk_002"],
                    "cardinality": 3,
                }
            }
        }
        save_json(sample_data, hypergraph_file)

        retriever = HypergraphRetriever(hypergraph_file)
        result = retriever.search("role of chlorophyll in light absorption", max_hyperedges=1)

        assert len(result.concepts) >= 1
        assert any(c.name == "Chlorophyll" for c in result.concepts)
        assert len(result.hyperedges) == 1
        assert result.hyperedges[0].hyperedge_id == "H1"
        assert "chunk_002" in result.sources


def test_hybrid_retriever_e2e():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        tmp_path = Path(tmp_dir)
        chroma_dir = tmp_path / "chroma"
        hypergraph_file = tmp_path / "hypergraph.json"

        # Setup vector retriever
        semantic_retriever = SemanticRetriever(
            collection_name="test_hybrid_col",
            persist_directory=chroma_dir
        )
        sample_chunk = Chunk(
            chunk_id="chunk_h_001",
            doc_id="doc_h",
            chunk_index=0,
            content="Photosynthesis converts water and carbon dioxide into glucose and oxygen.",
            word_count=10,
            token_count_approx=13,
            start_char=0,
            end_char=70,
            chunking_strategy=ChunkingStrategy.SEMANTIC,
            metadata={"source_file": "doc_h.txt"},
        )
        semantic_retriever.index_chunks([sample_chunk])

        # Setup hypergraph retriever
        sample_hypergraph_data = {
            "metadata": {"num_nodes": 2, "num_hyperedges": 1},
            "concepts": {
                "Water": {"concept_id": "Water", "name": "Water", "entity_type": "Molecule", "description": "H2O molecule", "source_chunk_ids": ["chunk_h_001"]},
                "Oxygen": {"concept_id": "Oxygen", "name": "Oxygen", "entity_type": "Molecule", "description": "O2 gas", "source_chunk_ids": ["chunk_h_001"]},
            },
            "hyperedges": {
                "H_water_ox": {
                    "hyperedge_id": "H_water_ox",
                    "label": "water_splitting",
                    "concepts": ["Water", "Oxygen"],
                    "description": "Splitting water produces oxygen gas.",
                    "source_chunk_ids": ["chunk_h_001"],
                    "cardinality": 2,
                }
            }
        }
        save_json(sample_hypergraph_data, hypergraph_file)
        hypergraph_retriever = HypergraphRetriever(hypergraph_file)

        hybrid_retriever = HybridRetriever(
            semantic_retriever=semantic_retriever,
            hypergraph_retriever=hypergraph_retriever
        )

        output_dict = hybrid_retriever.retrieve("How does water split to form oxygen?", top_k_semantic=1, top_k_hyperedges=1)

        # Validate required schema keys
        assert "query" in output_dict
        assert "chunks" in output_dict
        assert "concepts" in output_dict
        assert "hyperedges" in output_dict
        assert "sources" in output_dict

        assert len(output_dict["chunks"]) == 1
        assert output_dict["chunks"][0]["chunk_id"] == "chunk_h_001"
        assert output_dict["chunks"][0]["retrieval_method"] == "semantic"
        assert "chunk_h_001" in output_dict["sources"]
