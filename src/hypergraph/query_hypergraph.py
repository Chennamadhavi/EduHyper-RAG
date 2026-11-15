"""
Hypergraph Query Engine for EduHyperRAG.
Provides fast retrieval for concept nodes, hyperedge relationships, neighbor concepts,
multi-concept hyperedge intersections, source chunk IDs, and hyperedge cardinality.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union
import hypernetx as hnx
from src.config import config
from src.utils.file_io import read_json
from src.utils.logger import get_logger

logger = get_logger("query_hypergraph")


class EduHypergraphQueryEngine:
    """Query Engine operating over serialized EduHypergraph data."""

    def __init__(self, hypergraph_json_path: Optional[Union[str, Path]] = None):
        self.json_path = (
            Path(hypergraph_json_path)
            if hypergraph_json_path
            else config.knowledge_base_dir / "hypergraph.json"
        )
        self.concepts: Dict[str, Dict[str, Any]] = {}
        self.hyperedges: Dict[str, Dict[str, Any]] = {}
        self.metadata: Dict[str, Any] = {}
        self.hnx_graph: Optional[hnx.Hypergraph] = None
        
        if self.json_path.exists():
            self.load_hypergraph(self.json_path)

    def load_hypergraph(self, json_path: Union[str, Path]) -> None:
        """Loads serialized hypergraph JSON and reconstructs HyperNetX graph."""
        path = Path(json_path)
        if not path.exists():
            raise FileNotFoundError(f"Serialized hypergraph file not found: {path}")

        data = read_json(path)
        self.metadata = data.get("metadata", {})
        self.concepts = data.get("concepts", {})
        self.hyperedges = data.get("hyperedges", {})

        # Reconstruct HyperNetX graph
        hnx_dict = {
            hid: edge["concepts"] for hid, edge in self.hyperedges.items()
        }
        self.hnx_graph = hnx.Hypergraph(hnx_dict)
        logger.info(
            f"Loaded hypergraph from {path} ({len(self.concepts)} nodes, {len(self.hyperedges)} hyperedges)."
        )

    def get_hyperedges_containing_concept(self, concept_name: str) -> List[Dict[str, Any]]:
        """
        Retrieves all hyperedges containing the specified concept.

        Args:
            concept_name: Target concept name or ID.

        Returns:
            List of hyperedge data dictionaries.
        """
        target = concept_name.strip()
        matched: List[Dict[str, Any]] = []

        for hid, edge in self.hyperedges.items():
            if any(m.lower() == target.lower() for m in edge["concepts"]):
                matched.append(edge)

        return matched

    def get_neighboring_concepts(self, concept_name: str) -> List[str]:
        """
        Retrieves 1-hop neighbor concepts connected via shared hyperedges.

        Args:
            concept_name: Target concept name.

        Returns:
            List of unique neighboring concept names (excluding target concept).
        """
        target = concept_name.strip()
        neighbors: Set[str] = set()

        for edge in self.get_hyperedges_containing_concept(target):
            for m in edge["concepts"]:
                if m.lower() != target.lower():
                    neighbors.add(m)

        return sorted(list(neighbors))

    def get_hyperedges_for_multiple_concepts(
        self, concept_names: List[str], match_mode: str = "all"
    ) -> List[Dict[str, Any]]:
        """
        Retrieves hyperedges involving multiple query concepts.

        Args:
            concept_names: List of query concept names.
            match_mode: 'all' (intersection) or 'any' (union).

        Returns:
            List of matching hyperedge data dictionaries.
        """
        if not concept_names:
            return []

        targets = {c.strip().lower() for c in concept_names}
        matched: List[Dict[str, Any]] = []

        for hid, edge in self.hyperedges.items():
            edge_concepts = {m.lower() for m in edge["concepts"]}
            if match_mode == "all":
                if targets.issubset(edge_concepts):
                    matched.append(edge)
            elif match_mode == "any":
                if not targets.isdisjoint(edge_concepts):
                    matched.append(edge)
            else:
                raise ValueError("match_mode must be either 'all' or 'any'")

        return matched

    def get_source_chunk_ids(self, identifier: str) -> List[str]:
        """
        Returns supported source chunk IDs for a concept name or hyperedge ID.

        Args:
            identifier: Concept name or Hyperedge ID.

        Returns:
            List of chunk IDs.
        """
        target = identifier.strip()

        # Check concepts first
        for cid, concept in self.concepts.items():
            if cid.lower() == target.lower() or concept["name"].lower() == target.lower():
                return concept.get("source_chunk_ids", [])

        # Check hyperedges
        for hid, edge in self.hyperedges.items():
            if hid.lower() == target.lower() or edge.get("label", "").lower() == target.lower():
                return edge.get("source_chunk_ids", [])

        return []

    def get_hyperedge_size(self, hyperedge_id: str) -> int:
        """
        Calculates and returns the size/order (cardinality) of a specified hyperedge.

        Args:
            hyperedge_id: Hyperedge identifier.

        Returns:
            Number of concepts in the hyperedge.
        """
        target = hyperedge_id.strip()
        if target in self.hyperedges:
            return len(self.hyperedges[target]["concepts"])
        
        for hid, edge in self.hyperedges.items():
            if edge.get("label", "").lower() == target.lower():
                return len(edge["concepts"])

        raise KeyError(f"Hyperedge not found: {hyperedge_id}")
