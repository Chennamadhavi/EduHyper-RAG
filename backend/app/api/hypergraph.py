"""
Hypergraph Explorer API Router for EduHyper-RAG.
Provides structural hypergraph inspection, concept node degrees,
multi-concept hyperedge relationships, and visualization metadata.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from backend.app.api.deps import get_current_user
from backend.app.schemas.hypergraph import (
    ConceptDetailResponse,
    HypergraphEdge,
    HypergraphGraphResponse,
    HypergraphMetadata,
    HypergraphNode,
)
from src.config import config
from src.database.models import get_document_by_doc_id
from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine
from src.utils.logger import get_logger

logger = get_logger("hypergraph_api")
router = APIRouter()


def _get_hypergraph_path(doc_id: str) -> Path:
    """Finds the serialized hypergraph JSON file for a given document."""
    # 1. Direct document-specific hypergraph
    doc_path = config.knowledge_base_dir / f"hypergraph_{doc_id}.json"
    if doc_path.exists():
        return doc_path

    # 2. Check for sanitized doc_id variants
    clean_id = doc_id.replace(" ", "_").replace("?", "").replace("/", "_")
    alt_path = config.knowledge_base_dir / f"hypergraph_{clean_id}.json"
    if alt_path.exists():
        return alt_path

    # 3. Global fallback hypergraph
    fallback_path = config.knowledge_base_dir / "hypergraph.json"
    if fallback_path.exists():
        return fallback_path

    raise FileNotFoundError(f"Hypergraph file not found for document '{doc_id}'")


@router.get(
    "/documents/{doc_id}",
    response_model=HypergraphGraphResponse,
    summary="Get complete hypergraph data for a document",
)
async def get_document_hypergraph(
    doc_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns full concept nodes, hyperedge relationships, and complexity metrics
    for the requested document.
    """
    doc = get_document_by_doc_id(doc_id)
    filename = doc.get("filename") if doc else None

    try:
        json_path = _get_hypergraph_path(doc_id)
    except FileNotFoundError:
        # Check if doc exists in database
        if not doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document '{doc_id}' not found.",
            )
        # Empty graph structure if not yet processed
        return HypergraphGraphResponse(
            doc_id=doc_id,
            filename=filename,
            metadata=HypergraphMetadata(
                num_nodes=0,
                num_hyperedges=0,
                largest_hyperedge_id=None,
                largest_hyperedge_size=0,
                num_high_order=0,
                num_pairwise=0,
            ),
            nodes=[],
            hyperedges=[],
            has_image=False,
        )

    try:
        engine = EduHypergraphQueryEngine(json_path)
    except Exception as e:
        logger.exception(f"Failed to load hypergraph for doc '{doc_id}': {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error reading serialized hypergraph data.",
        )

    # 1. Compute node degrees (incident hyperedges)
    node_degrees: Dict[str, int] = {c_name: 0 for c_name in engine.concepts}
    for edge in engine.hyperedges.values():
        for c in edge.get("concepts", []):
            if c in node_degrees:
                node_degrees[c] += 1

    # 2. Format nodes
    formatted_nodes: List[HypergraphNode] = []
    for c_id, c_data in engine.concepts.items():
        formatted_nodes.append(
            HypergraphNode(
                id=c_id,
                name=c_data.get("name", c_id),
                entity_type=c_data.get("entity_type", "Concept"),
                description=c_data.get("description"),
                source_chunk_ids=c_data.get("source_chunk_ids", []),
                degree=node_degrees.get(c_id, 0),
            )
        )

    # 3. Format hyperedges and calculate high-order vs pairwise metrics
    num_high_order = 0
    num_pairwise = 0
    formatted_edges: List[HypergraphEdge] = []

    for hid, edge in engine.hyperedges.items():
        concepts = edge.get("concepts", [])
        cardinality = len(concepts)
        is_high = cardinality >= 3
        if is_high:
            num_high_order += 1
        elif cardinality == 2:
            num_pairwise += 1

        formatted_edges.append(
            HypergraphEdge(
                hyperedge_id=hid,
                label=edge.get("label", "co_occurs_with"),
                concepts=concepts,
                cardinality=cardinality,
                description=edge.get("description"),
                source_chunk_ids=edge.get("source_chunk_ids", []),
                is_high_order=is_high,
            )
        )

    # 4. Check for generated visualization plot
    img_path = config.knowledge_base_dir / "hypergraph_visualization.png"
    has_image = img_path.exists()

    metadata = HypergraphMetadata(
        num_nodes=len(formatted_nodes),
        num_hyperedges=len(formatted_edges),
        largest_hyperedge_id=engine.metadata.get("largest_hyperedge_id"),
        largest_hyperedge_size=engine.metadata.get("largest_hyperedge_size", 0),
        num_high_order=num_high_order,
        num_pairwise=num_pairwise,
    )

    return HypergraphGraphResponse(
        doc_id=doc_id,
        filename=filename,
        metadata=metadata,
        nodes=formatted_nodes,
        hyperedges=formatted_edges,
        has_image=has_image,
    )


@router.get(
    "/documents/{doc_id}/concepts/{concept_name}",
    response_model=ConceptDetailResponse,
    summary="Get detailed concept node inspection",
)
async def get_concept_details(
    doc_id: str,
    concept_name: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns specific concept entity metadata, all connected hyperedges,
    and 1-hop neighbor concepts connected through shared hyperedges.
    """
    try:
        json_path = _get_hypergraph_path(doc_id)
        engine = EduHypergraphQueryEngine(json_path)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hypergraph file for document '{doc_id}' not found.",
        )

    # Find concept node (case-insensitive)
    matched_id = None
    matched_data = None
    target_clean = concept_name.strip().lower()

    for c_id, c_data in engine.concepts.items():
        if c_id.lower() == target_clean or c_data.get("name", "").lower() == target_clean:
            matched_id = c_id
            matched_data = c_data
            break

    if not matched_id or not matched_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept '{concept_name}' not found in hypergraph.",
        )

    # Connected hyperedges
    raw_edges = engine.get_hyperedges_containing_concept(matched_id)
    connected_edges: List[HypergraphEdge] = []
    for edge in raw_edges:
        concepts = edge.get("concepts", [])
        connected_edges.append(
            HypergraphEdge(
                hyperedge_id=edge.get("hyperedge_id", ""),
                label=edge.get("label", "co_occurs_with"),
                concepts=concepts,
                cardinality=len(concepts),
                description=edge.get("description"),
                source_chunk_ids=edge.get("source_chunk_ids", []),
                is_high_order=len(concepts) >= 3,
            )
        )

    # Neighbors
    neighbors = engine.get_neighboring_concepts(matched_id)

    node = HypergraphNode(
        id=matched_id,
        name=matched_data.get("name", matched_id),
        entity_type=matched_data.get("entity_type", "Concept"),
        description=matched_data.get("description"),
        source_chunk_ids=matched_data.get("source_chunk_ids", []),
        degree=len(connected_edges),
    )

    return ConceptDetailResponse(
        concept=node,
        connected_hyperedges=connected_edges,
        neighbors=neighbors,
    )


@router.get(
    "/documents/{doc_id}/image",
    summary="Get generated HyperNetX visualization image",
)
async def get_hypergraph_image(
    doc_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
):
    """
    Returns the static matplotlib/HyperNetX PNG visualization plot if available.
    """
    img_path = config.knowledge_base_dir / "hypergraph_visualization.png"
    if not img_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hypergraph plot image not found.",
        )
    return FileResponse(img_path, media_type="image/png")
