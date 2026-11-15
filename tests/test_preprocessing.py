"""
Unit tests for Phase 1 Text Preprocessing and Chunking modules.
"""

import os
import tempfile
from pathlib import Path
import pytest

from src.preprocessing.cleaner import TextCleaner
from src.preprocessing.chunker import (
    Chunk,
    ChunkingStrategy,
    FixedLengthChunker,
    SemanticChunker,
    count_tokens,
)
from src.preprocessing.pipeline import PreprocessingPipeline
from src.utils.file_io import read_json, read_text_file, save_json, save_text_file


def test_text_cleaner():
    cleaner = TextCleaner(strip_page_numbers=True)
    raw_sample = "Photosyn-\nthesis occurs in  chloroplasts. Page 12 of 45\n\n\n--- Page 3 ---\nIt requires light."
    cleaned = cleaner.clean(raw_sample)
    
    assert "photosynthesis" in cleaned.lower()
    assert "Page 12 of 45" not in cleaned
    assert "--- Page 3 ---" not in cleaned
    assert "  " not in cleaned  # no double space


def test_fixed_length_chunker():
    chunker = FixedLengthChunker(chunk_size=10, chunk_overlap=2, use_tokens=False)
    sample_text = "Word " * 25  # 25 words
    chunks = chunker.chunk(sample_text, doc_id="test_doc")
    
    assert len(chunks) > 1
    assert chunks[0].chunking_strategy == ChunkingStrategy.FIXED_LENGTH
    assert chunks[0].doc_id == "test_doc"
    assert chunks[0].chunk_id.startswith("test_doc_fixed_")
    assert chunks[0].word_count <= 10


def test_semantic_chunker():
    chunker = SemanticChunker(target_chunk_size=20, max_chunk_size=40)
    sample_text = (
        "# Section 1: Introduction\n\n"
        "Photosynthesis is the process by which plants convert light energy into chemical energy. "
        "It takes place in chloroplasts containing chlorophyll pigments.\n\n"
        "## Section 2: Light Reactions\n\n"
        "Light reactions occur in the thylakoid membranes where PSII and PSI operate in series."
    )
    chunks = chunker.chunk(sample_text, doc_id="test_sem")
    
    assert len(chunks) >= 1
    assert chunks[0].chunking_strategy == ChunkingStrategy.SEMANTIC
    assert "section" in chunks[0].metadata


def test_file_io_helpers():
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        text_file = tmp_path / "test.txt"
        json_file = tmp_path / "test.json"
        
        save_text_file("Hello EduHyperRAG", text_file)
        assert read_text_file(text_file) == "Hello EduHyperRAG"
        
        data = {"key": "value", "count": 42}
        save_json(data, json_file)
        assert read_json(json_file) == data


def test_preprocessing_pipeline_e2e():
    with tempfile.TemporaryDirectory() as tmp_dir:
        raw_dir = Path(tmp_dir) / "raw"
        processed_dir = Path(tmp_dir) / "processed"
        chunks_dir = Path(tmp_dir) / "chunks"
        raw_dir.mkdir(parents=True)
        
        sample_doc = raw_dir / "sample_bio.txt"
        save_text_file("# Cellular Respiration\n\nRespiration breaks down glucose to generate ATP in mitochondria.", sample_doc)
        
        pipeline = PreprocessingPipeline()
        # Override config paths for isolated testing
        from src.config import config
        original_processed = config.processed_data_dir
        original_chunks = config.chunks_data_dir
        
        config.processed_data_dir = processed_dir
        config.chunks_data_dir = chunks_dir
        
        try:
            summaries = pipeline.process_directory(raw_dir)
            assert len(summaries) == 1
            assert summaries[0]["doc_id"] == "sample_bio"
            assert summaries[0]["fixed_chunks_count"] >= 1
            assert summaries[0]["semantic_chunks_count"] >= 1
            assert Path(summaries[0]["fixed_chunks_path"]).exists()
            assert Path(summaries[0]["semantic_chunks_path"]).exists()
        finally:
            config.processed_data_dir = original_processed
            config.chunks_data_dir = original_chunks
