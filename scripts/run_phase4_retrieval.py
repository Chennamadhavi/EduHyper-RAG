"""
Script to execute Phase 4: Combined Semantic + Hypergraph Retrieval.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import config
from src.retrieval.hybrid_retriever import HybridRetriever
from src.retrieval.semantic_retriever import SemanticRetriever
from src.utils.logger import get_logger

logger = get_logger("run_phase4")


def main():
    print("=" * 80)
    print("      EDUHYPERRAG - PHASE 4: COMBINED SEMANTIC + HYPERGRAPH RETRIEVAL      ")
    print("=" * 80)

    chunks_file = config.chunks_data_dir / "photosynthesis_chapter_semantic_chunks.json"
    hypergraph_file = config.knowledge_base_dir / "hypergraph.json"

    if not chunks_file.exists():
        logger.error(f"Chunks file not found at: {chunks_file}")
        logger.error("Please run Phase 1 first via: python scripts/run_phase1_preprocessing.py")
        sys.exit(1)

    if not hypergraph_file.exists():
        logger.error(f"Hypergraph file not found at: {hypergraph_file}")
        logger.error("Please run Phase 3 first via: python scripts/run_phase3_hypergraph.py")
        sys.exit(1)

    # 1. Index document chunks in ChromaDB
    logger.info("Indexing semantic chunks into ChromaDB...")
    semantic_retriever = SemanticRetriever()
    indexed_count = semantic_retriever.index_from_file(chunks_file)
    logger.info(f"Indexed {indexed_count} chunk(s) into ChromaDB.")

    # 2. Instantiate HybridRetriever
    hybrid_retriever = HybridRetriever(semantic_retriever=semantic_retriever)

    # 3. Test queries as specified in requirements
    test_queries = [
        "How does water participate in photosynthesis?",
        "What is the role of chlorophyll?",
        "How are light reactions connected to oxygen production?",
    ]

    for idx, query in enumerate(test_queries, 1):
        print("\n" + "=" * 80)
        print(f"QUERY {idx}: \"{query}\"")
        print("=" * 80)

        result = hybrid_retriever.retrieve(query, top_k_semantic=2, top_k_hyperedges=3)

        # A. Semantic Chunks Output
        print("\n--- A. SEMANTIC VECTOR RETRIEVAL (ChromaDB) ---")
        for chunk in result["chunks"]:
            print(f"Chunk ID        : {chunk['chunk_id']}")
            print(f"Relevance Score : {chunk['relevance_score']}")
            print(f"Method          : {chunk['retrieval_method']}")
            snippet = chunk['content'].replace('\n', ' ')[:140]
            print(f"Snippet         : {snippet}...\n")

        # B. Hypergraph Concepts Output
        print("--- B. HYPERGRAPH CONCEPT RETRIEVAL (Nodes) ---")
        for concept in result["concepts"][:4]:
            print(f"Concept Node   : {concept['name']} ({concept['entity_type']})")
            print(f"Description    : {concept['description']}")
            print(f"Source Chunks  : {concept['source_chunk_ids']}\n")

        # C. Hypergraph Hyperedges Output
        print("--- C. HYPERGRAPH HYPEREDGE RETRIEVAL (Edges) ---")
        for edge in result["hyperedges"]:
            print(f"Hyperedge ID   : {edge['hyperedge_id']} ({edge['label']})")
            print(f"Cardinality    : {edge['cardinality']}")
            print(f"Member Concepts: {edge['concepts']}")
            print(f"Description    : {edge['description']}")
            print(f"Source Chunks  : {edge['source_chunk_ids']}\n")

        # D. Source Chunk Traceability
        print("--- D. ALL PRESERVED SOURCE CHUNK IDs ---")
        print(f"Sources: {result['sources']}")
        print("-" * 80)

    print("\nPhase 4 completed successfully!")


if __name__ == "__main__":
    main()
