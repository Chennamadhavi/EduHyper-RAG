"""
Script to execute Phase 1: Text Preprocessing and Chunking.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.config import config
from src.preprocessing.pipeline import PreprocessingPipeline
from src.utils.logger import get_logger

logger = get_logger("run_phase1")

def main():
    print("=" * 70)
    print("      EDUHYPERRAG - PHASE 1: TEXT PREPROCESSING & CHUNKING      ")
    print("=" * 70)
    
    logger.info("Initializing Preprocessing Pipeline...")
    pipeline = PreprocessingPipeline()
    
    raw_dir = config.raw_data_dir
    logger.info(f"Target raw data directory: {raw_dir}")
    
    summaries = pipeline.process_directory(raw_dir)
    
    print("\n" + "-" * 70)
    print("                   PHASE 1 EXECUTION SUMMARY                    ")
    print("-" * 70)
    for s in summaries:
        print(f"Document ID           : {s['doc_id']}")
        print(f"Source File           : {s['source_file']}")
        print(f"Raw Character Count   : {s['raw_char_count']}")
        print(f"Cleaned Character Count: {s['cleaned_char_count']}")
        print(f"Fixed-Length Chunks   : {s['fixed_chunks_count']}")
        print(f"Semantic Chunks       : {s['semantic_chunks_count']}")
        print(f"Cleaned Output Path   : {s['cleaned_text_path']}")
        print(f"Fixed Chunks JSON     : {s['fixed_chunks_path']}")
        print(f"Semantic Chunks JSON  : {s['semantic_chunks_path']}")
        print("-" * 70)
        
    print("\nPhase 1 completed successfully!")

if __name__ == "__main__":
    main()
