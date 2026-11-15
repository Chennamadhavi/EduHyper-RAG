"""
Global Configuration for EduHyperRAG System.
Handles loading environment variables, defining project directory paths,
and setting default hyperparameter configurations.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file if available
load_dotenv()

llm_api_key: Optional[str] = Field(
    default=os.getenv("LLM_API_KEY", "")
)

llm_model_name: str = Field(
    default=os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash")
)

# Determine project root directory (directory containing src/ or parent of src/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

class AppConfig(BaseModel):
    """Application configuration schema."""
    
    # Project Paths
    project_root: Path = Field(default=PROJECT_ROOT)
    data_dir: Path = Field(default=PROJECT_ROOT / "data")
    raw_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "raw")
    processed_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "processed")
    chunks_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "chunks")
    knowledge_base_dir: Path = Field(default=PROJECT_ROOT / "data" / "knowledge_base")
    
    # Database & Extension Paths
    db_path: Path = Field(default=PROJECT_ROOT / "data" / "eduhyperrag.db")
    courses_data_dir: Path = Field(default=PROJECT_ROOT / "data" / "courses")
    
    # Chunking Defaults
    default_chunk_size: int = Field(default=int(os.getenv("DEFAULT_CHUNK_SIZE", "1200")))
    default_chunk_overlap: int = Field(default=int(os.getenv("DEFAULT_CHUNK_OVERLAP", "100")))
    min_chunk_size: int = Field(default=100)
    
    # LLM Settings (for subsequent phases)
    llm_api_key: Optional[str] = Field(default=os.getenv("LLM_API_KEY", ""))
    llm_model_name: str = Field(default=os.getenv("LLM_MODEL_NAME", "gemini-2.5-flash"))
    
    # Logging
    log_level: str = Field(default=os.getenv("LOG_LEVEL", "INFO"))

    def ensure_directories(self) -> None:
        """Create necessary project directories if they do not exist."""
        for path in [
            self.data_dir,
            self.raw_data_dir,
            self.processed_data_dir,
            self.chunks_data_dir,
            self.knowledge_base_dir,
            self.courses_data_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

# Create singleton global configuration instance
config = AppConfig()
config.ensure_directories()

