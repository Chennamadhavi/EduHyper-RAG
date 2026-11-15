"""
Pydantic schemas for document ingestion and metadata retrieval.
"""

from typing import Optional
from pydantic import BaseModel, Field


class DocumentResponse(BaseModel):
    """Document metadata representation."""
    id: int
    doc_id: str
    filename: str
    course_id: int
    course_code: Optional[str] = None
    course_title: Optional[str] = None
    uploaded_by: int
    status: str
    num_chunks: int = 0
    num_concepts: int = 0
    num_hyperedges: int = 0
    created_at: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    """Response returned upon completing document ingestion."""
    doc_id: str
    filename: str
    status: str
    num_chunks: int
    num_concepts: int
    num_hyperedges: int
    hypergraph_json_path: Optional[str] = None
    message: str = "Document successfully ingested and indexed into knowledge base."
