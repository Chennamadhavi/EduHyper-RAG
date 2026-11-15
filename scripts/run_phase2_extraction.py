"""
Script to execute Phase 2: LLM-Based Concept and Hyperedge Extraction.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import config
from src.extraction.pipeline import ExtractionPipeline
from src.utils.logger import get_logger

logger = get_logger("run_phase2")

def main():
    print("=" * 70)
    print("      EDUHYPERRAG - PHASE 2: CONCEPT & HYPEREDGE EXTRACTION     ")
    print("=" * 70)

    chunks_dir = config.chunks_data_dir
    semantic_chunks_file = chunks_dir / "photosynthesis_chapter_semantic_chunks.json"

    if not semantic_chunks_file.exists():
        logger.error(f"Semantic chunks file not found at: {semantic_chunks_file}")
        logger.error("Please run Phase 1 first via: python scripts/run_phase1_preprocessing.py")
        sys.exit(1)

    logger.info("Initializing Extraction Pipeline...")
    pipeline = ExtractionPipeline()

    summary = pipeline.process_chunks_file(semantic_chunks_file)

    print("\n" + "-" * 70)
    print("                   PHASE 2 EXECUTION SUMMARY                    ")
    print("-" * 70)
    print(f"Document ID                 : {summary['doc_id']}")
    print(f"Chunks Processed            : {summary['chunks_processed']}")
    print(f"Total Unique Entities ($V$)   : {summary['total_entities']}")
    print(f"Low-Order Relations ($E_low$) : {summary['total_low_order_relations']}")
    print(f"High-Order Hyperedges ($E_high$): {summary['total_high_order_hyperedges']}")
    print(f"Avg Hyperedge Cardinality   : {summary['avg_hyperedge_cardinality']}")
    print(f"Extractions Output Path     : {summary['extraction_output_path']}")
    print("-" * 70)

    print("\nPhase 2 completed successfully!")

if __name__ == "__main__":
    main()
