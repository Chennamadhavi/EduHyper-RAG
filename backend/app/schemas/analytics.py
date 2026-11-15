"""
Pydantic schemas for Teacher Analytics and Student Learning Progress.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RecentQuestionItem(BaseModel):
    """Detailed record of a student interaction for analytics monitoring."""
    id: Optional[int] = None
    user_query: str
    timestamp: str
    confidence_level: Optional[str] = "MEDIUM"
    support_score: float = 0.0
    verification_decision: str = "VERIFIED"
    student_name: Optional[str] = None
    filename: Optional[str] = None
    course_code: Optional[str] = None


class CourseAnalyticsItem(BaseModel):
    """Per-course engagement and quality metrics."""
    course_id: int
    course_code: str
    title: str
    total_queries: int = 0
    avg_support_score: float = 0.0
    flagged_queries: int = 0
    enrolled_count: int = 0


class TeacherAnalyticsResponse(BaseModel):
    """Comprehensive instructor analytics summary."""
    total_courses: int
    total_documents: int
    total_queries: int
    avg_support_score: float
    flagged_queries: int
    hallucination_rate_pct: float
    courses_breakdown: List[CourseAnalyticsItem] = Field(default_factory=list)
    decisions_breakdown: Dict[str, int] = Field(default_factory=dict)
    confidence_breakdown: Dict[str, int] = Field(default_factory=dict)
    recent_questions: List[RecentQuestionItem] = Field(default_factory=list)
    flagged_questions: List[RecentQuestionItem] = Field(default_factory=list)


class StudentCourseProgressItem(BaseModel):
    """Student progress within a specific course."""
    course_id: int
    course_code: str
    title: str
    queries_count: int
    avg_support_score: float


class StudentProgressResponse(BaseModel):
    """Personalized student learning analytics and grounding progress."""
    student_id: int
    student_name: str
    total_queries: int
    enrolled_courses_count: int
    avg_support_score: float
    verified_rate_pct: float
    decisions_breakdown: Dict[str, int] = Field(default_factory=dict)
    confidence_breakdown: Dict[str, int] = Field(default_factory=dict)
    course_progress: List[StudentCourseProgressItem] = Field(default_factory=list)
    recent_activity: List[RecentQuestionItem] = Field(default_factory=list)


class BenchmarkRow(BaseModel):
    """Empirical baseline comparison metrics row."""
    architecture: str
    correctness: float
    faithfulness: float
    context_recall: float
    kmr: float
    her: float
    latency_ms: float


class BenchmarkResponse(BaseModel):
    """Phase 9 benchmark evaluation results."""
    title: str
    dataset_size: int
    rows: List[BenchmarkRow]
