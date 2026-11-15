"""
Hypergraph Construction Engine for EduHyperRAG using HyperNetX.

Constructs a document-specific hypergraph from extracted concepts
and hyperedges (cardinality >= 2), calculates graph analytics,
and serializes the result to JSON.

The implementation is subject-agnostic and supports any uploaded
educational document.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import re

import hypernetx as hnx
from pydantic import BaseModel, Field

from src.config import config
from src.utils.file_io import read_json, save_json
from src.utils.logger import get_logger


logger = get_logger("build_hypergraph")


class ConceptNode(BaseModel):
    """Concept node representation in the hypergraph."""

    concept_id: str
    name: str
    entity_type: str = "Concept"
    description: str = ""
    source_chunk_ids: List[str] = Field(default_factory=list)


class HyperedgeData(BaseModel):
    """Hyperedge representation connecting 2 or more concepts."""

    hyperedge_id: str
    label: str
    concepts: List[str]
    description: str = ""
    source_chunk_ids: List[str] = Field(default_factory=list)
    cardinality: int = 0


class EduHypergraphBuilder:
    """
    Builder class for HyperNetX Hypergraph construction
    and serialization.

    Each uploaded document can have its own concepts,
    hyperedges, and serialized hypergraph.
    """

    def __init__(self):
        self.concepts: Dict[str, ConceptNode] = {}
        self.hyperedges: Dict[str, HyperedgeData] = {}
        self.hnx_graph: Optional[hnx.Hypergraph] = None

    # =========================================================
    # PHASE 3A
    # Prepare document-specific hypergraph input files
    # =========================================================

    def prepare_input_files_from_extractions(
        self,
        extractions_path: Union[str, Path],
        doc_id: Optional[str] = None,
    ) -> tuple[Path, Path]:
        """
        Converts Phase 2 extraction JSON into hypergraph input files.

        When doc_id is provided, the generated files are:

            concepts_<doc_id>.json
            hyperedges_<doc_id>.json

        This prevents different uploaded documents from
        overwriting each other's intermediate hypergraph data.

        If doc_id is not provided, the function falls back to:

            concepts.json
            hyperedges.json

        This preserves compatibility with older CLI scripts.
        """

        ext_path = Path(extractions_path)

        if not ext_path.exists():
            raise FileNotFoundError(
                f"Extractions file not found: {ext_path}"
            )

        # -----------------------------------------------------
        # Read Phase 2 extraction output
        # -----------------------------------------------------

        data = read_json(ext_path)

        concepts_list: List[Dict[str, Any]] = []
        hyperedges_list: List[Dict[str, Any]] = []

        # -----------------------------------------------------
        # Convert extracted entities into concept nodes
        # -----------------------------------------------------

        for ent in data.get("entities", []):
            name = str(
                ent.get("name", "")
            ).strip()

            if not name:
                continue

            concepts_list.append(
                {
                    "concept_id": name,
                    "name": name,
                    "entity_type": ent.get(
                        "entity_type",
                        "Concept",
                    ),
                    "description": ent.get(
                        "description",
                        "",
                    ),
                    "source_chunk_ids": ent.get(
                        "source_chunk_ids",
                        [],
                    ),
                }
            )

        # -----------------------------------------------------
        # Convert low-order relations
        # -----------------------------------------------------

        for rel in data.get(
            "low_order_relations",
            [],
        ):
            src = str(
                rel.get("source_entity", "")
            ).strip()

            tgt = str(
                rel.get("target_entity", "")
            ).strip()

            if not src or not tgt:
                continue

            rel_id = rel.get(
                "relation_id",
                f"E_low_{len(hyperedges_list):03d}",
            )

            hyperedges_list.append(
                {
                    "hyperedge_id": rel_id,
                    "label": rel.get(
                        "relation_type",
                        "pairwise_relation",
                    ),
                    "concepts": [
                        src,
                        tgt,
                    ],
                    "description": rel.get(
                        "description",
                        "",
                    ),
                    "source_chunk_ids": rel.get(
                        "source_chunk_ids",
                        [],
                    ),
                    "cardinality": 2,
                }
            )

        # -----------------------------------------------------
        # Convert high-order hyperedges
        # -----------------------------------------------------

        for hyp in data.get(
            "high_order_hyperedges",
            [],
        ):
            members = [
                str(member).strip()
                for member in hyp.get(
                    "member_entities",
                    [],
                )
                if str(member).strip()
            ]

            # A hyperedge must contain at least 2 concepts.
            if len(members) < 2:
                continue

            hyp_id = hyp.get(
                "hyperedge_id",
                f"H_{len(hyperedges_list):03d}",
            )

            hyperedges_list.append(
                {
                    "hyperedge_id": hyp_id,
                    "label": hyp.get(
                        "relation_type",
                        "high_order_hyperedge",
                    ),
                    "concepts": members,
                    "description": hyp.get(
                        "description",
                        "",
                    ),
                    "source_chunk_ids": hyp.get(
                        "source_chunk_ids",
                        [],
                    ),
                    "cardinality": len(members),
                }
            )

        # -----------------------------------------------------
        # Create document-specific output paths
        # -----------------------------------------------------

        if doc_id:
            safe_doc_id = re.sub(
                r"[^a-zA-Z0-9_-]",
                "_",
                str(doc_id),
            ).strip("_")

            if not safe_doc_id:
                safe_doc_id = "document"

            concepts_path = (
                config.knowledge_base_dir
                / f"concepts_{safe_doc_id}.json"
            )

            hyperedges_path = (
                config.knowledge_base_dir
                / f"hyperedges_{safe_doc_id}.json"
            )

        else:
            # Backward compatibility for old scripts.
            concepts_path = (
                config.knowledge_base_dir
                / "concepts.json"
            )

            hyperedges_path = (
                config.knowledge_base_dir
                / "hyperedges.json"
            )

        # -----------------------------------------------------
        # Save generated files
        # -----------------------------------------------------

        save_json(
            concepts_list,
            concepts_path,
        )

        save_json(
            hyperedges_list,
            hyperedges_path,
        )

        logger.info(
            f"Saved {len(concepts_list)} concepts to "
            f"{concepts_path}"
        )

        logger.info(
            f"Saved {len(hyperedges_list)} hyperedges to "
            f"{hyperedges_path}"
        )

        return concepts_path, hyperedges_path

    # =========================================================
    # PHASE 3B
    # Build HyperNetX graph
    # =========================================================

    def build_from_files(
        self,
        concepts_path: Union[str, Path],
        hyperedges_path: Union[str, Path],
    ) -> hnx.Hypergraph:
        """
        Loads concepts and hyperedges JSON files and constructs
        a HyperNetX Hypergraph.
        """

        c_path = Path(concepts_path)
        h_path = Path(hyperedges_path)

        if not c_path.exists():
            raise FileNotFoundError(
                f"Concepts file not found: {c_path}"
            )

        if not h_path.exists():
            raise FileNotFoundError(
                f"Hyperedges file not found: {h_path}"
            )

        # -----------------------------------------------------
        # Load JSON data
        # -----------------------------------------------------

        raw_concepts = read_json(c_path)
        raw_hyperedges = read_json(h_path)

        # -----------------------------------------------------
        # Reset builder state
        # -----------------------------------------------------

        self.concepts = {}
        self.hyperedges = {}
        self.hnx_graph = None

        # -----------------------------------------------------
        # Build concept dictionary
        # -----------------------------------------------------

        for c in raw_concepts:
            node = ConceptNode(**c)

            self.concepts[node.concept_id] = node

        # -----------------------------------------------------
        # Build hyperedge dictionary
        # -----------------------------------------------------

        hnx_dict: Dict[str, List[str]] = {}

        for h in raw_hyperedges:

            concepts = h.get(
                "concepts",
                [],
            )

            # Remove duplicate concepts while
            # preserving original order.
            unique_members = list(
                dict.fromkeys(
                    concepts
                )
            )

            # Hyperedge requires at least 2 concepts.
            if len(unique_members) < 2:
                logger.warning(
                    f"Skipping hyperedge "
                    f"'{h.get('hyperedge_id')}' "
                    f"with less than 2 members: "
                    f"{unique_members}"
                )
                continue

            # -------------------------------------------------
            # Ensure all referenced concepts exist
            # -------------------------------------------------

            for member in unique_members:

                if member not in self.concepts:

                    self.concepts[member] = (
                        ConceptNode(
                            concept_id=member,
                            name=member,
                            entity_type="Concept",
                            description=(
                                f"Auto-generated concept "
                                f"node for {member}"
                            ),
                            source_chunk_ids=h.get(
                                "source_chunk_ids",
                                [],
                            ),
                        )
                    )

            # -------------------------------------------------
            # Create HyperedgeData
            # -------------------------------------------------

            edge = HyperedgeData(
                hyperedge_id=h[
                    "hyperedge_id"
                ],
                label=h.get(
                    "label",
                    h["hyperedge_id"],
                ),
                concepts=unique_members,
                description=h.get(
                    "description",
                    "",
                ),
                source_chunk_ids=h.get(
                    "source_chunk_ids",
                    [],
                ),
                cardinality=len(
                    unique_members
                ),
            )

            self.hyperedges[
                edge.hyperedge_id
            ] = edge

            hnx_dict[
                edge.hyperedge_id
            ] = unique_members

        # -----------------------------------------------------
        # Construct HyperNetX graph
        # -----------------------------------------------------

        self.hnx_graph = hnx.Hypergraph(
            hnx_dict
        )

        logger.info(
            f"Constructed HyperNetX Hypergraph "
            f"with {len(self.hnx_graph.nodes)} nodes "
            f"and {len(self.hnx_graph.edges)} hyperedges."
        )

        return self.hnx_graph

    # =========================================================
    # PHASE 3C
    # Save serialized hypergraph
    # =========================================================

    def save_hypergraph_json(
        self,
        output_path: Optional[
            Union[str, Path]
        ] = None,
    ) -> Path:
        """
        Serializes the constructed hypergraph into JSON.

        If output_path is provided, that path is used.

        Otherwise the legacy default is:
            data/knowledge_base/hypergraph.json
        """

        if self.hnx_graph is None:
            raise ValueError(
                "Hypergraph has not been constructed yet. "
                "Call build_from_files() first."
            )

        # -----------------------------------------------------
        # Determine output path
        # -----------------------------------------------------

        if output_path:
            out_path = Path(
                output_path
            )
        else:
            out_path = (
                config.knowledge_base_dir
                / "hypergraph.json"
            )

        # Make sure destination directory exists.
        out_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        # -----------------------------------------------------
        # Calculate largest hyperedge
        # -----------------------------------------------------

        largest_hyperedge_id = ""
        max_cardinality = 0

        for (
            hyperedge_id,
            edge,
        ) in self.hyperedges.items():

            if (
                edge.cardinality
                > max_cardinality
            ):
                max_cardinality = (
                    edge.cardinality
                )

                largest_hyperedge_id = (
                    hyperedge_id
                )

        # -----------------------------------------------------
        # Serialize graph
        # -----------------------------------------------------

        serialized_data = {
            "metadata": {
                "num_nodes": len(
                    self.hnx_graph.nodes
                ),
                "num_hyperedges": len(
                    self.hnx_graph.edges
                ),
                "largest_hyperedge_id": (
                    largest_hyperedge_id
                ),
                "largest_hyperedge_size": (
                    max_cardinality
                ),
            },
            "concepts": {
                concept_id: node.model_dump()
                for (
                    concept_id,
                    node,
                ) in self.concepts.items()
            },
            "hyperedges": {
                hyperedge_id: edge.model_dump()
                for (
                    hyperedge_id,
                    edge,
                ) in self.hyperedges.items()
            },
        }

        # -----------------------------------------------------
        # Save JSON
        # -----------------------------------------------------

        save_json(
            serialized_data,
            out_path,
        )

        logger.info(
            f"Saved serialized hypergraph to "
            f"{out_path}"
        )

        return out_path