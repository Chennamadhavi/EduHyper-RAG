"""
Pydantic schemas for Hypergraph exploration, concept nodes, and multi-concept hyperedges.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class HypergraphNode(BaseModel):
    """Concept node in the educational hypergraph."""
    id: str
    name: str
    entity_type: str = "Concept"
    description: Optional[str] = None
    source_chunk_ids: List[str] = Field(default_factory=list)
    degree: int = 0


class HypergraphEdge(BaseModel):
    """Hyperedge connecting two or more concept entities."""
    hyperedge_id: str
    label: str
    concepts: List[str]
    cardinality: int
    description: Optional[str] = None
    source_chunk_ids: List[str] = Field(default_factory=list)
    is_high_order: bool = False


class HypergraphMetadata(BaseModel):
    """Structural summary of hypergraph complexity."""
    num_nodes: int
    num_hyperedges: int
    largest_hyperedge_id: Optional[str] = None
    largest_hyperedge_size: int = 0
    num_high_order: int = 0  # cardinality >= 3
    num_pairwise: int = 0    # cardinality == 2


class HypergraphGraphResponse(BaseModel):
    """Full hypergraph data payload for visualization and exploration."""
    doc_id: str
    filename: Optional[str] = None
    metadata: HypergraphMetadata
    nodes: List[HypergraphNode] = Field(default_factory=list)
    hyperedges: List[HypergraphEdge] = Field(default_factory=list)
    has_image: bool = False


class ConceptDetailResponse(BaseModel):
    """Detailed concept inspection with connected hyperedges and neighbor nodes."""
    concept: HypergraphNode
    connected_hyperedges: List[HypergraphEdge] = Field(default_factory=list)
    neighbors: List[str] = Field(default_factory=list)
