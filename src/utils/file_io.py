"""
File I/O utilities for reading and writing text, JSON, and PDF files safely.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Union
from src.utils.logger import get_logger

logger = get_logger("file_io")

def read_text_file(file_path: Union[str, Path]) -> str:
    """Reads and returns text content from a text file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Failed to read file {path}: {str(e)}")
        raise

def save_text_file(content: str, file_path: Union[str, Path]) -> Path:
    """Saves text content to a specified file path."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Saved text file to {path}")
        return path
    except Exception as e:
        logger.error(f"Failed to save text file {path}: {str(e)}")
        raise

def save_json(data: Union[Dict[str, Any], List[Any]], file_path: Union[str, Path], indent: int = 2) -> Path:
    """Saves data structure as a formatted JSON file."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        logger.info(f"Saved JSON output to {path}")
        return path
    except Exception as e:
        logger.error(f"Failed to save JSON to {path}: {str(e)}")
        raise

def read_json(file_path: Union[str, Path]) -> Any:
    """Reads and parses JSON content from a file."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to read JSON from {path}: {str(e)}")
        raise

def read_pdf_file(file_path: Union[str, Path]) -> str:
    """Extracts text content from a PDF file using PyMuPDF (fitz)."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(path)
        extracted_text = []
        for page_num, page in enumerate(doc, start=1):
            text = page.get_text("text")
            if text:
                extracted_text.append(text)
        doc.close()
        full_text = "\n\n".join(extracted_text)
        logger.info(f"Successfully extracted {len(extracted_text)} pages from PDF: {path}")
        return full_text
    except ImportError:
        logger.error("PyMuPDF (fitz) is not installed. Please install PyMuPDF.")
        raise
    except Exception as e:
        logger.error(f"Error reading PDF file {path}: {str(e)}")
        raise
