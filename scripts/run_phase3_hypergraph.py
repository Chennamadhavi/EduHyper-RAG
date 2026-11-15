"""
Script to execute Phase 3: Hypergraph Construction, Analytics, Querying, and Visualization.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import config
from src.hypergraph.build_hypergraph import EduHypergraphBuilder
from src.hypergraph.query_hypergraph import EduHypergraphQueryEngine
from src.hypergraph.visualize_hypergraph import print_text_hypergraph_summary, visualize_hypergraph
from src.utils.logger import get_logger

logger = get_logger("run_phase3")


def main():
    print("=" * 75)
    print("         EDUHYPERRAG - PHASE 3: HYPERGRAPH CONSTRUCTION & QUERIES        ")
    print("=" * 75)

    extractions_file = config.processed_data_dir / "extractions_photosynthesis_chapter.json"
    if not extractions_file.exists():
        logger.error(f"Extractions file not found: {extractions_file}")
        logger.error("Please run Phase 2 first via: python scripts/run_phase2_extraction.py")
        sys.exit(1)

    logger.info("Initializing EduHypergraphBuilder...")
    builder = EduHypergraphBuilder()

    # 1. Generate inputs data/knowledge_base/concepts.json and hyperedges.json
    concepts_json, hyperedges_json = builder.prepare_input_files_from_extractions(extractions_file)

    # 2. Build HyperNetX hypergraph
    hnx_graph = builder.build_from_files(concepts_json, hyperedges_json)

    # 3. Save serialized hypergraph.json
    output_json = builder.save_hypergraph_json()

    # 4. Instantiate Query Engine & execute demonstration queries
    query_engine = EduHypergraphQueryEngine(output_json)

    print("\n" + "-" * 75)
    print("                   PHASE 3 CONSTRUCTION STATISTICS                    ")
    print("-" * 75)
    print(f"Number of Concept Nodes ($V$) : {len(query_engine.concepts)}")
    print(f"Number of Hyperedges ($E$)     : {len(query_engine.hyperedges)}")
    print(f"Largest Hyperedge ID         : {query_engine.metadata.get('largest_hyperedge_id')}")
    print(f"Largest Hyperedge Size/Order : {query_engine.metadata.get('largest_hyperedge_size')}")
    print("-" * 75)

    # Demonstrate Example Multi-Entity Relationship
    print("\n--- EXAMPLE MULTI-ENTITY RELATIONSHIP (CARDINALITY >= 3) ---")
    multi_entity_edges = [e for e in query_engine.hyperedges.values() if len(e['concepts']) >= 3]
    if multi_entity_edges:
        sample_edge = multi_entity_edges[0]
        print(f"Hyperedge ID     : {sample_edge['hyperedge_id']}")
        print(f"Label            : {sample_edge['label']}")
        print(f"Member Concepts  : {sample_edge['concepts']}")
        print(f"Cardinality/Size : {sample_edge['cardinality']}")
        print(f"Description      : {sample_edge['description']}")
        print(f"Source Chunk IDs : {sample_edge['source_chunk_ids']}")
    print("-" * 75)

    # Demonstrate Query Capabilities
    print("\n--- DEMONSTRATION HYPERGRAPH QUERIES ---")
    query_concept = "Photosystem II"
    print(f"1. Query: Hyperedges containing '{query_concept}':")
    matched_edges = query_engine.get_hyperedges_containing_concept(query_concept)
    for me in matched_edges:
        print(f"   - [{me['hyperedge_id']}] {me['label']} (Concepts: {me['concepts']})")

    print(f"\n2. Query: 1-Hop Neighbor Concepts of '{query_concept}':")
    neighbors = query_engine.get_neighboring_concepts(query_concept)
    print(f"   Neighbors: {neighbors}")

    multi_query = ["Photosystem II", "P680"]
    print(f"\n3. Query: Hyperedges containing ALL of {multi_query}:")
    multi_matched = query_engine.get_hyperedges_for_multiple_concepts(multi_query, match_mode="all")
    for mm in multi_matched:
        print(f"   - [{mm['hyperedge_id']}] {mm['label']} (Concepts: {mm['concepts']})")

    # 5. Visualization
    logger.info("Generating Hypergraph Visualization...")
    vis_image_path = visualize_hypergraph()
    print(f"\nVisualization saved to: {vis_image_path}")

    # Print ASCII summary map
    print_text_hypergraph_summary()

    print("\nPhase 3 completed successfully!")

if __name__ == "__main__":
    main()
