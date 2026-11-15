"""
Unit tests for Phase 3 Hypergraph Construction and Querying.
"""

import tempfile
from pathlib import Path
import pytest

from src.hypergraph.build_hypergraph import EduHypergraphBuilder
from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine
from src.utils.file_io import read_json, save_json


def test_hypergraph_build_and_query():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        concepts_path = tmp_path / "concepts.json"
        hyperedges_path = tmp_path / "hyperedges.json"
        output_json = tmp_path / "hypergraph.json"

        # Create dummy concept data
        sample_concepts = [
            {"concept_id": "Water", "name": "Water", "entity_type": "Molecule", "description": "H2O", "source_chunk_ids": ["c1"]},
            {"concept_id": "Light", "name": "Light", "entity_type": "Factor", "description": "Solar photon energy", "source_chunk_ids": ["c1"]},
            {"concept_id": "Chlorophyll", "name": "Chlorophyll", "entity_type": "Pigment", "description": "Green pigment", "source_chunk_ids": ["c1"]},
            {"concept_id": "Oxygen", "name": "Oxygen", "entity_type": "Molecule", "description": "O2 gas", "source_chunk_ids": ["c1"]},
        ]
        save_json(sample_concepts, concepts_path)

        # Create dummy hyperedge data (H1 connects 4 concepts)
        sample_hyperedges = [
            {
                "hyperedge_id": "H1",
                "label": "water_photolysis",
                "concepts": ["Water", "Light", "Chlorophyll", "Oxygen"],
                "description": "Splitting water using light and chlorophyll.",
                "source_chunk_ids": ["c1"],
                "cardinality": 4,
            },
            {
                "hyperedge_id": "E1",
                "label": "light_absorption",
                "concepts": ["Light", "Chlorophyll"],
                "description": "Chlorophyll absorbs light.",
                "source_chunk_ids": ["c1"],
                "cardinality": 2,
            },
        ]
        save_json(sample_hyperedges, hyperedges_path)

        # Build hypergraph
        builder = EduHypergraphBuilder()
        builder.build_from_files(concepts_path, hyperedges_path)
        builder.save_hypergraph_json(output_json)

        assert output_json.exists()

        # Query hypergraph
        engine = EduHypergraphQueryEngine(output_json)
        assert len(engine.concepts) == 4
        assert len(engine.hyperedges) == 2

        # Query hyperedges containing concept
        edges_for_water = engine.get_hyperedges_containing_concept("Water")
        assert len(edges_for_water) == 1
        assert edges_for_water[0]["hyperedge_id"] == "H1"

        # Query neighboring concepts
        neighbors_for_water = engine.get_neighboring_concepts("Water")
        assert "Light" in neighbors_for_water
        assert "Chlorophyll" in neighbors_for_water
        assert "Oxygen" in neighbors_for_water
        assert "Water" not in neighbors_for_water

        # Query multiple concepts intersection
        multi_edges = engine.get_hyperedges_for_multiple_concepts(["Light", "Chlorophyll"], match_mode="all")
        assert len(multi_edges) == 2  # H1 and E1 both contain Light and Chlorophyll

        multi_all_water = engine.get_hyperedges_for_multiple_concepts(["Water", "Oxygen"], match_mode="all")
        assert len(multi_all_water) == 1
        assert multi_all_water[0]["hyperedge_id"] == "H1"

        # Query source chunk IDs
        chunks = engine.get_source_chunk_ids("Water")
        assert chunks == ["c1"]

        # Query hyperedge size
        size = engine.get_hyperedge_size("H1")
        assert size == 4
