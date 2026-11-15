"""
Pydantic schemas for the EduHyper-RAG FastAPI backend.
"""

from typing import Dict
from pydantic import BaseModel, Field


class ComponentStatus(BaseModel):
    """Status description of an individual backend component."""
    status: str = Field(..., description="Component health state (e.g., 'healthy', 'available', 'uninitialized')")
    detail: str = Field(..., description="Safe human-readable detail without secrets or stack traces")


class HealthResponse(BaseModel):
    """Schema for the GET /api/health endpoint response."""
    status: str = Field(..., description="Overall API health status ('ok' or 'degraded')")
    app_name: str = Field(..., description="Application service name")
    environment: str = Field(..., description="Active runtime environment")
    version: str = Field(..., description="Application semantic version")
    components: Dict[str, ComponentStatus] = Field(..., description="Subsystem operational statuses")


from backend.app.schemas.auth import (
    UserRegisterRequest,
    UserLoginRequest,
    UserResponse,
    TokenResponse,
)
from backend.app.schemas.course import (
    CourseCreateRequest,
    CourseResponse,
    CourseEnrollRequest,
)
from backend.app.schemas.document import (
    DocumentResponse,
    DocumentUploadResponse,
)
from backend.app.schemas.tutor import (
    TutorQueryRequest,
    TutorQueryResponse,
    QAHistoryItem,
)
from backend.app.schemas.hypergraph import (
    HypergraphNode,
    HypergraphEdge,
    HypergraphMetadata,
    HypergraphGraphResponse,
    ConceptDetailResponse,
)
from backend.app.schemas.analytics import (
    TeacherAnalyticsResponse,
    StudentProgressResponse,
    BenchmarkResponse,
    RecentQuestionItem,
    CourseAnalyticsItem,
    StudentCourseProgressItem,
    BenchmarkRow,
)

__all__ = [
    "ComponentStatus",
    "HealthResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserResponse",
    "TokenResponse",
    "CourseCreateRequest",
    "CourseResponse",
    "CourseEnrollRequest",
    "DocumentResponse",
    "DocumentUploadResponse",
    "TutorQueryRequest",
    "TutorQueryResponse",
    "QAHistoryItem",
    "HypergraphNode",
    "HypergraphEdge",
    "HypergraphMetadata",
    "HypergraphGraphResponse",
    "ConceptDetailResponse",
    "TeacherAnalyticsResponse",
    "StudentProgressResponse",
    "BenchmarkResponse",
    "RecentQuestionItem",
    "CourseAnalyticsItem",
    "StudentCourseProgressItem",
    "BenchmarkRow",
]
