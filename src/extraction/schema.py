"""
Pydantic Schemas for Concept, Relation, and Hyperedge Extraction.
Enforces strict typing, source tracking, and hyperedge cardinality validation.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class EntityType(str, Enum):
    ORGANELLE = "Organelle"
    MOLECULE = "Molecule"
    ENZYME = "Enzyme"
    PIGMENT = "Pigment"
    PROCESS = "Process"
    PATHWAY = "Pathway"
    PROTEIN = "Protein"
    CONCEPT = "Concept"
    FACTOR = "Factor"


class ExtractedEntity(BaseModel):
    """Represents a discrete domain concept/entity (Hypergraph Node)."""
    entity_id: str = Field(..., description="Unique entity identifier")
    name: str = Field(..., description="Canonical entity name")
    entity_type: EntityType = Field(default=EntityType.CONCEPT, description="Category of the entity")
    description: str = Field(..., description="Educational summary/definition of the entity")
    source_chunk_ids: List[str] = Field(default_factory=list, description="List of source chunk IDs where entity appears")


class LowOrderRelation(BaseModel):
    """Represents a pairwise binary relation between 2 entities (Standard Graph Edge)."""
    relation_id: str = Field(..., description="Unique relation identifier")
    source_entity: str = Field(..., description="Name or ID of source entity")
    target_entity: str = Field(..., description="Name or ID of target entity")
    relation_type: str = Field(..., description="Type of relationship e.g., 'transfers_electrons_to', 'catalyzes'")
    description: str = Field(..., description="Detailed description of the pairwise interaction")
    source_chunk_ids: List[str] = Field(default_factory=list, description="Source chunk IDs supporting this relation")


class HighOrderHyperedge(BaseModel):
    """Represents a multi-entity correlation connecting >= 3 entities (Hyperedge)."""
    hyperedge_id: str = Field(..., description="Unique hyperedge identifier")
    member_entities: List[str] = Field(..., description="Names or IDs of 3 or more entities involved in this hyperedge")
    relation_type: str = Field(..., description="Type/Name of the multi-entity process/pathway")
    description: str = Field(..., description="Comprehensive multi-way correlation description")
    cardinality: int = Field(..., description="Number of member entities connected by hyperedge")
    source_chunk_ids: List[str] = Field(default_factory=list, description="Source chunk IDs supporting this hyperedge")

    @field_validator("cardinality", mode="before")
    def compute_cardinality(cls, v: Any, info: Any) -> int:
        members = info.data.get("member_entities", [])
        return len(members) if members else v

    @field_validator("member_entities")
    def validate_min_cardinality(cls, v: List[str]) -> List[str]:
        # Deduplicate while preserving order
        unique_members = list(dict.fromkeys(v))
        if len(unique_members) < 3:
            raise ValueError(f"High-order hyperedges must connect at least 3 distinct entities, got {len(unique_members)}: {unique_members}")
        return unique_members


class ChunkExtractionResult(BaseModel):
    """Extraction output for a single chunk."""
    chunk_id: str
    doc_id: str
    entities: List[ExtractedEntity] = Field(default_factory=list)
    low_order_relations: List[LowOrderRelation] = Field(default_factory=list)
    high_order_hyperedges: List[HighOrderHyperedge] = Field(default_factory=list)


class KnowledgeBaseExtractions(BaseModel):
    """Aggregated extraction output for an entire document or corpus."""
    doc_id: str
    entities: List[ExtractedEntity] = Field(default_factory=list)
    low_order_relations: List[LowOrderRelation] = Field(default_factory=list)
    high_order_hyperedges: List[HighOrderHyperedge] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
