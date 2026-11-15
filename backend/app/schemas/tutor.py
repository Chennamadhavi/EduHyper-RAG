"""
Pydantic schemas for AI Tutor question answering, verification, and history.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TutorQueryRequest(BaseModel):
    """Payload for submitting a question to the AI Tutor."""
    query: str = Field(..., min_length=3, max_length=1000, description="Educational question")
    doc_id: str = Field(..., description="Target document ID for scoped retrieval")
    course_id: int = Field(..., description="Target course ID")
    max_iterations: Optional[int] = Field(default=2, ge=1, le=5, description="Max LangGraph verification cycles")
    min_support_score: Optional[float] = Field(default=0.7, ge=0.0, le=1.0, description="Minimum claim support threshold")


class TutorQueryResponse(BaseModel):
    """Grounded, verified answer response with explainability metadata."""
    query: str
    answer: str
    confidence_level: str
    support_score: float
    verification_decision: str
    verification_reasoning: Optional[str] = None
    supporting_chunks: List[str] = Field(default_factory=list)
    supporting_hyperedges: List[str] = Field(default_factory=list)
    retrieved_concepts: List[str] = Field(default_factory=list)
    retrieved_chunk_details: List[Dict[str, Any]] = Field(default_factory=list)
    hallucination_report: Optional[Dict[str, Any]] = None
    explainability_report: Optional[Dict[str, Any]] = None
    doc_id: str
    course_id: int


class QAHistoryItem(BaseModel):
    """Individual QA interaction record from student history."""
    id: int
    student_id: int
    doc_id: str
    course_id: int
    user_query: str
    generated_answer: str
    confidence_level: Optional[str] = "MEDIUM"
    support_score: Optional[float] = 0.0
    verification_decision: Optional[str] = "VERIFIED"
    filename: Optional[str] = None
    course_code: Optional[str] = None
    created_at: Optional[str] = None
